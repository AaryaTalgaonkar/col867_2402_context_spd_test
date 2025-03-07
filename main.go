package main

import (
	"context"
	"crypto/tls"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"io/ioutil"
	"net/http"
	"os"
	"time"

	"github.com/gorilla/websocket"
)

const (
	minMessageSize       = 1 << 10
	maxScaledMessageSize = 1 << 20
	maxMessageSize       = 1 << 24
	maxRuntime           = 10 * time.Second
	measureInterval      = 250 * time.Millisecond
	fractionForScaling   = 16
)

func downloadTest(ctx context.Context, conn *websocket.Conn, file *os.File) error {

	if err := conn.SetReadDeadline(time.Now().Add(maxRuntime)); err != nil {
		return err
	}
	conn.SetReadLimit(maxMessageSize)
	ticker := time.NewTicker(measureInterval)
	logged :=0
	defer ticker.Stop()
	for ctx.Err() == nil {
		kind, reader, err := conn.NextReader()
		if err != nil {
			return err
		}
		if kind == websocket.TextMessage {
			data, err := ioutil.ReadAll(reader)
			if err != nil {
				return err
			}
			if logged == 0{
				var msg map[string]interface{}
				if err := json.Unmarshal(data, &msg); err != nil {
					fmt.Printf("Error unmarshaling JSON: %v\n", err)
					continue
				}
				
				// Access the UUID
				if connectionInfo, ok := msg["ConnectionInfo"].(map[string]interface{}); ok {
					if uuid, ok := connectionInfo["UUID"].(string); ok {
						fmt.Fprintf(file,"UUID: %s, Test: Download\n", uuid)
					} else {
						fmt.Println("UUID not found or not a string")
					}
				} else {
					fmt.Println("ConnectionInfo not found or not a map")
				}
				logged += 1
			}

			continue
		}
		_, err1 := io.Copy(ioutil.Discard, reader)
		if err1 != nil {
			return err
		}
	}
	return nil
}

func newMessage(n int) (*websocket.PreparedMessage, error) {
	return websocket.NewPreparedMessage(websocket.BinaryMessage, make([]byte, n))
}

func uploadTest(ctx context.Context, conn *websocket.Conn, file *os.File) error {
	var total int64
	if err := conn.SetWriteDeadline(time.Now().Add(maxRuntime)); err != nil {
		return err
	}
	size := minMessageSize
	message, err := newMessage(size)
	if err != nil {
		return err
	}
	ticker := time.NewTicker(measureInterval)
	defer ticker.Stop()

	go func() {
		for ctx.Err() == nil {
			kind, reader, err := conn.NextReader()
			if err != nil {
				return
			}
			if kind == websocket.TextMessage {
				data, err := ioutil.ReadAll(reader)
				if err != nil {
					return
				}

				var msg map[string]interface{}
				if err := json.Unmarshal(data, &msg); err != nil {
					fmt.Printf("Error unmarshaling JSON: %v\n", err)
					continue
				}
				
				// Access the UUID
				if connectionInfo, ok := msg["ConnectionInfo"].(map[string]interface{}); ok {
					if uuid, ok := connectionInfo["UUID"].(string); ok {
						fmt.Fprintf(file,"UUID: %s, Test: Upload\n", uuid)
					} else {
						fmt.Println("UUID not found or not a string")
					}
				} else {
					fmt.Println("ConnectionInfo not found or not a map")
				}
				break
			}
			_, err1 := io.Copy(ioutil.Discard, reader)
			if err1 != nil {
				return
			}
		}
	}()


	for ctx.Err() == nil {
		if err := conn.WritePreparedMessage(message); err != nil {
			return err
		}
		total += int64(size)
		if int64(size) >= maxScaledMessageSize || int64(size) >= (total/fractionForScaling) {
			continue
		}
		size <<= 1
		if message, err = newMessage(size); err != nil {
			return err
		}
	}
	return nil
}

var (
	flagDownload = flag.String("download", "", "Download URL")
	flagNoVerify = flag.Bool("no-verify", false, "No TLS verify")
	flagUpload   = flag.String("upload", "", "Upload URL")

)

func dialer(ctx context.Context, URL string) (*websocket.Conn, error) {
	dialer := websocket.Dialer{
		TLSClientConfig: &tls.Config{
			InsecureSkipVerify: *flagNoVerify,
		},
		ReadBufferSize:  maxMessageSize,
		WriteBufferSize: maxMessageSize,
	}
	headers := http.Header{}
	headers.Add("Sec-WebSocket-Protocol", "net.measurementlab.ndt.v7")
	conn, _, err := dialer.DialContext(ctx, URL, headers)
	return conn, err
}

func warnx(err error, testname string) {
	fmt.Printf(`{"Failure":"%s","Test":"%s"}`+"\n\n", err.Error(), testname)
}

func errx(exitcode int, err error, testname string) {
	warnx(err, testname)
	os.Exit(exitcode)
}

const (
	locateDownloadURL = "wss:///ndt/v7/download"
	locateUploadURL   = "wss:///ndt/v7/upload"
)

type locateResponseResult struct {
	URLs map[string]string `json:"urls"`
}

type locateResponse struct {
	Results []locateResponseResult `json:"results"`
}

func locate(ctx context.Context) error {
	// If you don't specify any option then we use locate. Otherwise we assume
	// you're testing locally and we only do what you asked us to do.
	if *flagDownload != "" || *flagUpload != "" {
		return nil
	}
	resp, err := http.Get("https://locate.measurementlab.net/v2/nearest/ndt/ndt7")
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	data, err := ioutil.ReadAll(io.LimitReader(resp.Body, 1<<20))
	if err != nil {
		return err
	}
	var locate locateResponse
	if err := json.Unmarshal(data, &locate); err != nil {
		return err
	}
	if len(locate.Results) < 1 {
		return errors.New("too few entries")
	}
	// TODO(bassosimone): support flagRoundTrip here when locate v2 is ready
	*flagDownload = locate.Results[0].URLs[locateDownloadURL]
	*flagUpload = locate.Results[0].URLs[locateUploadURL]
	return nil
}

func main() {
	// Open the file for writing
	file, err := os.Create("output.csv")
	if err != nil {
		fmt.Printf("Error creating file: %v\n", err)
		return
	}
	defer file.Close()
	for i := 0; i < 2; i++ {
		flag.Parse()
		ctx := context.Background()
		var (
			conn *websocket.Conn
			err  error
		)
		if err = locate(ctx); err != nil {
			errx(1, err, "locate")
		}
		if *flagDownload != "" {
			if conn, err = dialer(ctx, *flagDownload); err != nil {
				errx(1, err, "download")
			}
			if err = downloadTest(ctx, conn,file); err != nil {
				warnx(err, "download")
			}
		}
		if *flagUpload != "" {
			if conn, err = dialer(ctx, *flagUpload); err != nil {
				errx(1, err, "upload")
			}
			if err = uploadTest(ctx, conn,file); err != nil {
				warnx(err, "upload")
			}
		}
	}
}
