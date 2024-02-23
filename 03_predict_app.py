from flask import Flask, render_template, request, jsonify
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)


# 仮のモデル予測関数
def model_predict(input_data):
    # ここでモデルをロードし、予測を行う
    # 今回は仮の予測結果を返す
    return input_data * 2

@app.route('/predict', methods=['POST'])
def predict():
    if request.method == 'POST':
        input_data = request.form['input_data']
        prediction = model_predict(int(input_data))
        return render_template('result.html', prediction=prediction)
