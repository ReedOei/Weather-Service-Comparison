DATE="$1"

if [ -z "$2" ]; then
    VAR="precip_chance"
else
    VAR="$2"
fi

if [ -z "$3" ]; then
    ANALYZE_DIR="./analyze/daily/"
else
    ANALYZE_DIR="./analyze/$3/"
fi

python collect_data.py dump date="$DATE" graph=True x=forecasted_time y="$VAR" analyze_dir="$ANALYZE_DIR"
