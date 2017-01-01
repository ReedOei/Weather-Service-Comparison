if [ -z "$1" ]; then
    TYPE="scatter"
else
    TYPE="$1"
fi

if [ -z "$2" ]; then
    ANALYZE_DIR="./analyze/daily/"
else
    ANALYZE_DIR="./analyze/$2/"
fi

if [ -z "$3" ]; then
    METHOD="decay"
else
    METHOD="$3"
fi

python collect_data.py combine o=forecast.txt analyze_dir="$ANALYZE_DIR" method="$METHOD"
python collect_data.py dump graph y=precip_chance f=forecast.txt ymin=0 ymax=1 type="$TYPE"
