import os
from flask import Flask, request, jsonify
import pandas as pd
import io
from datetime import datetime

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "running",
        "service": "CSV Processor for Dify",
        "version": "1.0"
    })

@app.route('/process-csv', methods=['POST', 'OPTIONS'])
def process_csv():
    # CORS対応
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response
    
    try:
        # リクエストデータの取得
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        csv_string = data.get('csv_data', '')
        reduction_percentage = float(data.get('reduction_percentage', 0))
        
        # CSVデータの読み込み
        df = pd.read_csv(io.StringIO(csv_string))
        
        # 価格列を探す
        price_columns = ['price', 'Price', '価格', '販売価格', 'selling_price']
        price_column = None
        
        for col in price_columns:
            if col in df.columns:
                price_column = col
                break
        
        if price_column:
            # 値下げ処理
            df['original_price'] = df[price_column]
            df['new_price'] = (df[price_column] * (1 - reduction_percentage / 100))
            df['new_price'] = df['new_price'].round(0).astype(int)
            df['reduction_rate'] = f"{reduction_percentage}%"
            df['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            summary = {
                'total_rows': len(df),
                'reduction_percentage': reduction_percentage,
                'average_original_price': float(df['original_price'].mean()),
                'average_new_price': float(df['new_price'].mean())
            }
        else:
            summary = {
                'warning': 'Price column not found',
                'available_columns': df.columns.tolist()
            }
        
        response = jsonify({
            'status': 'success',
            'processed_csv': df.to_csv(index=False),
            'summary': summary
        })
        
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
