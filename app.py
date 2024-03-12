from flask import Flask, render_template, request
import pickle
import numpy as np
import plotly.express as px
import pandas as pd

app = Flask(__name__)

# Predict product
def Predict_product(to_predict_list):
    to_predict = np.array(to_predict_list).reshape(1, 5)
    loaded_model = pickle.load(open("model.pkl", "rb"))
    result = loaded_model.predict(to_predict)
    return result[0]

# predict total
def Predict_total(input_data):
    to_predict = np.array(input_data).reshape(1, 7)
    loaded_model = pickle.load(open("rf_model.pkl", "rb"))
    result_predict = loaded_model.predict(to_predict)
    return result_predict[0]

# render trang index
@app.route('/')
def index():
    return render_template('index.html')

# render trang dự đoán sản phẩm
@app.route('/predict_product')
def product():
    return render_template('predict_product.html')

# render trang dự đoán total
@app.route('/predict_total')
def total():
    return render_template('predict_total.html')

# render trang report
@app.route('/report')
def report():
    return render_template('report.html')

# render trang predict_many_total
@app.route('/many_total')
def many_total():
    return render_template('predict_many_total.html')

# Chuyển số thành tên sản phẩm
def predict(result):
    if result == 0:
        return "Health and beauty"
    elif result == 1:
        return "Electronic accessories"
    elif result == 2:
        return "Home and lifestyle"
    elif result == 3:
        return "Sports and travel"
    elif result == 4:
        return "Food and beverages"
    else:
        return "Fashion accessories"

# Dự đoán tên sản phẩm
@app.route('/product', methods=['POST'])
def result_product():
    if request.method == 'POST':
        to_predict_list = []
        fields = ['price', 'quantity', 'taxedPrice', 'costPrice', 'total']
        for field in fields:
            if field in request.form:
                to_predict_list.append(request.form[field])
            else:
                to_predict_list.append(0)
        input_predict_name = list(map(float, to_predict_list))
        result = Predict_product(input_predict_name)
        prediction = predict(result)
        return render_template("result_product.html", prediction=prediction)
    
# Dự đoán 1 total
@app.route('/total', methods=['POST'])
def result_total():
    if request.method == 'POST':
        to_predict_list = []
        Branch = np.random.randint(1, 4)
        City = np.random.randint(1, 4)
        Product = np.random.randint(1, 7)
        fields = [Branch, City, Product,'price', 'quantity', 'taxedPrice', 'costPrice']
        for field in fields:
            if field in request.form:
                to_predict_list.append(request.form[field])
            else:
                to_predict_list.append(0)
        input_predict_total = list(map(float, to_predict_list))
        result = Predict_total(input_predict_total)
        prediction = result.round(2)
        return render_template("result_total.html", prediction=prediction)

# Trực quan file dữ liệu
@app.route('/visualization', methods=['POST'])
def visualization():
    file = request.files['data']
    if file.filename != '':
        df = pd.read_csv(file)
        # Tạo bảng tổng hợp dữ liệu theo và sản phẩm
        summary_data = df.groupby('Product').agg({'Total': 'sum'}).reset_index()

        # Trực quan hóa bảng tổng hợp bằng Plotly
        fig = px.bar(summary_data, x='Product', y='Total', color='Product',
                labels={'Total': 'Doanh Thu $', 'Product': 'Sản Phẩm'},
                height=600, width=1000)
        return render_template('report_chart.html', plot=fig.to_html(full_html=False))
    else:
        message = "Upload file"
        return render_template('no_file_report.html', message=message)
    
# Dự đoán nhiều sản phẩm trong 1 file
@app.route('/predict_many_total', methods=['POST'])
def predict_many_total():
    file = request.files['list_data']
    if file.filename != '':
        # Đọc file
        df = pd.read_csv(file)
        df.dropna(axis=1)
        # Xóa cột mục tiêu dự đoán Total
        df.drop('Total', axis=1, inplace=True)

        # Lấy tên sp trước khi mã hóa
        list_name_products = df['Product'].unique().tolist()

        # Tạo một từ điển để ánh xạ tên nhãn bắt đầu từ 0
        branch = {branch: label + 0 for label, branch in enumerate(df['Branch'].unique())}
        df['Branch'] = df['Branch'].map(branch)
        city = {city: label + 0 for label, city in enumerate(df['City'].unique())}
        df['City'] = df['City'].map(city)
        product = {product: label + 0 for label, product in enumerate(df['Product'].unique())}
        df['Product'] = df['Product'].map(product)

        # sum các giá trị của từng sảm phẩm vào result_df
        result_df = df.groupby('Product').agg({
            'Price': 'sum',
            'Quantity': 'sum',
            'Tax': 'sum',
            'Cogs': 'sum'
        }).reset_index()

        # Xóa cột Product và lấy chỉ lấy 2 số sau dấu chấm vd: 79815.6240 -> 79815.62
        scale_data = result_df.round(2)
        print(scale_data)

        predict = []
        # Lặp dự đoán các sản phẩm
        for index, row in scale_data.iterrows():
            branch = np.random.randint(0, len(df['Branch'].unique()))
            print("Branch", branch)
            city = np.random.randint(0, len(df['City'].unique()))
            print("City", city)
            # Ghép biến branch, city và row
            list_input_data = [branch, city, row.tolist()]
            # Bỏ dấu [] ở giữa list
            flattened_list = list_input_data[:2] + list_input_data[2]
            print(flattened_list)
            # Đưa dữ liệu vào mô hình dự đoán
            predict_result = Predict_total(flattened_list)
            print(predict_result)
            predict.append(predict_result.round(2))

        list_predict_result=pd.DataFrame({'Product': list_name_products, 'Total': predict})

        # Trực quan hóa bảng tổng hợp bằng Plotly
        fig = px.bar(list_predict_result, x='Product', y='Total', color='Product',
                     labels={'Product': 'Sản Phẩm', 'Total': 'Doanh thu ($)'}, height=600, width=1000)
        return render_template('result_many_total.html', bar=fig.to_html(full_html=False))
    else:
        message = "Upload file"
        return render_template('no_file_total.html', message=message)

if __name__ == '__main__':
    app.run(debug=True)
