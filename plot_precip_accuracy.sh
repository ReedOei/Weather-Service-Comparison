if [ -z "$1" ]; then
    INC="0.1"
else
    INC="$1"
fi

if [ -z "$2" ]; then
    METHOD="decay"
else
    METHOD="$2"
fi

if [ -z "$3" ]; then
    ANALYZE_DIR="analyze/daily/"
else
    ANALYZE_DIR="analyze/$3/"
fi

if [ "$3" == "hourly" ]; then
    JOIN_FUNCTION="round_hour"
else
    JOIN_FUNCTION="round_date"
fi

DATA_FUNCTION="precip_accuracy"

python collect_data.py combine o=forecast.txt analyze_dir="$ANALYZE_DIR" method="$METHOD"
python collect_data.py dump graph type="bar:$INC" join="$JOIN_FUNCTION" data="$DATA_FUNCTION" y=precip_chance,is_precip f=forecast.txt analyze_dir="analyze/currently/" ymin=0 ymax=1 xmin=0 xmax=1.1
