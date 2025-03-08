export CREDENTIALS_FILE="./ndt7-server/ ndt7speedtestcontextualization-50cfbf444c9b.json"
gcloud init
gcloud auth login --cred-file=$CREDENTIALS_FILE

# To check access is working with M-LAb data
gsutil ls -l gs://archive-measurement-lab/

# To save pcaps for a date in current directory
gsutil cp -r gs://archive-measurement-lab/ndt/pcap/2025/03/08/ . 
