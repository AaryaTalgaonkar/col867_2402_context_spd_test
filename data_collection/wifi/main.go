package main

import (
	"context"
	"crypto/tls"
	"encoding/json"
	"math/rand"
	"errors"
	"flag"
	"fmt"
	"io"
	"io/ioutil"
	"net/http"
	"os"
	"os/exec"
	"time"
	"strings"
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

func downloadTest(ctx context.Context, conn *websocket.Conn, file *os.File,machineName string) error {

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
						timestamp :=  time.Now().UTC().Format("150405")
						date := time.Now().UTC().Format("2006/01/02")
						fmt.Fprintf(file,"%s,%s,%s,%s\n",machineName,date,timestamp,uuid)
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

func uploadTest(ctx context.Context, conn *websocket.Conn, file *os.File,machineName string) error {
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
						timestamp :=  time.Now().UTC().Format("150405")
						date := time.Now().UTC().Format("2006/01/02")
						fmt.Fprintf(file,"%s,%s,%s,%s\n",machineName,date,timestamp, uuid)
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
	fmt.Printf(`{"Failure":"%s","Test":"%s"}`+"\n", err.Error(), testname)
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
	Machine string            `json:"machine"`
	URLs map[string]string `json:"urls"`
}

type locateResponse struct {
	Results []locateResponseResult `json:"results"`
}

func locate(ctx context.Context) (string, error) {
	// If you don't specify any option then we use locate. Otherwise we assume
	// you're testing locally and we only do what you asked us to do.
	resp, err := http.Get("https://locate.measurementlab.net/v2/nearest/ndt/ndt7")
	if err != nil {
		return "",err
	}
	defer resp.Body.Close()
	data, err := ioutil.ReadAll(io.LimitReader(resp.Body, 1<<20))
	if err != nil {
		return "",err
	}
	var locate locateResponse
	if err := json.Unmarshal(data, &locate); err != nil {
		return "",err
	}

	if len(locate.Results) < 1 {
		return "",errors.New("too few entries")
	}
	firstResult := locate.Results[0]
	machineName := strings.Split(firstResult.Machine, ".")[0]
	*flagDownload = locate.Results[0].URLs[locateDownloadURL]
	*flagUpload = locate.Results[0].URLs[locateUploadURL]
	return machineName,nil
}


// applyRandomShaping generates random traffic shaping parameters and executes the script
func applyShaping(direction string) error {
	rand.Seed(time.Now().UnixNano()) // Seed random generator

	// Generate random values
	rate := fmt.Sprintf("%dmbit", rand.Intn(5000)+1)      // 1 - 5000 Mbps
	delay := fmt.Sprintf("%dms", rand.Intn(491)+10)      // 10 - 500 ms
	jitter := fmt.Sprintf("%dms", rand.Intn(101))        // 0 - 100 ms
	loss := fmt.Sprintf("%.2f%%", rand.Float64()*5)     // 0% - 5%

	fmt.Println("Applying Traffic Shaping with:")
	fmt.Println("  - Direction:", direction)
	fmt.Println("  - Rate:", rate)
	fmt.Println("  - Delay:", delay)
	fmt.Println("  - Jitter:", jitter)
	fmt.Println("  - Packet Loss:", loss)

	// Execute shaping script
	cmd := exec.Command("bash", "./shaper.sh", "start", direction, rate, delay, jitter, loss)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	return cmd.Run()
}


// Stops traffic shaping
func stopShaping() error {
	fmt.Println("Stopping traffic shaping...")

	// Execute stop script
	cmd := exec.Command("bash", "./shaper.sh", "stop")
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	return cmd.Run()
}

func main() {
	filename := "output.csv"

	// Check if the file exists
	_, err := os.Stat(filename)
	isNewFile := os.IsNotExist(err) // True if the file does not exist

	// Open the file for appending, create if it doesn't exist
	file, err := os.OpenFile(filename, os.O_WRONLY|os.O_CREATE|os.O_APPEND, 0644)
	if err != nil {
		fmt.Printf("Error opening file: %v\n", err)
		return
	}
	defer file.Close()

	// If the file is newly created, write the header row
	if isNewFile {
		fmt.Fprintf(file, "Machine,Date,Timestamp,UUID\n")
	}

	for i := 0; i < 100; i++ {
		flag.Parse()
		ctx := context.Background()
		var (
			conn        *websocket.Conn
			err         error
			machineName string
		)
		for {
			machineName, err = locate(ctx)
			if err == nil {
				break // Exit loop if successful
			}
			errx(1,err, "locate")
		}
		// applyShaping("download")
		if *flagDownload != "" {
			for {
				conn, err = dialer(ctx, *flagDownload)
				if err == nil {
					break // Exit loop if no error
				}
				warnx(err, "download") // Handle error (adjust as needed)
			}
			if err = downloadTest(ctx, conn,file,machineName); err != nil {
				warnx(err, "download")
			}
		}
		fmt.Printf("Speedtest download %d conducted\n", i)
		// stopShaping()

		time.Sleep(3 * time.Second)

		// applyShaping("upload")
		if *flagUpload != "" {
			for {
				conn, err = dialer(ctx, *flagUpload)
				if err == nil {
					break // Exit loop if successful
				}
				warnx(err, "upload") // Handle error (adjust as needed)
			}
			if err = uploadTest(ctx, conn,file,machineName); err != nil {
				warnx(err, "upload")
			}
		}
		fmt.Printf("Speedtest upload %d conducted\n", i)
		// stopShaping()
		time.Sleep(3 * time.Second)
	}
}
