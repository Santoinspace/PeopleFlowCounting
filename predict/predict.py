import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA

def predict(df, future_steps):

    # 4. 划分数据集
    train_size = int(len(df) * 0.8)
    train, test = df[:train_size], df[train_size:]

    # 5. 选择模型
    model = ARIMA(train['Value'], order=(1, 1, 1))  # 选择合适的ARIMA阶数

    # 6. 拟合模型
    model_fit = model.fit()

    # 7. 模型评估
    predictions = model_fit.forecast(steps=len(test))
    rmse = np.sqrt(np.mean((predictions - test['Value'])**2))
    # print(f'RMSE: {rmse}')

    # 8. 预测未来值
    future_forecast = model_fit.forecast(steps=future_steps + len(test))
    # 9. 截取未来范围
    future_forecast = future_forecast[-future_steps:]
    
    # 日期格式转换
    echarts_data = {
        'Date': [],
        'Value': []
    }

    # 转换
    for index, row in future_forecast.iteritems():
        echarts_data['Date'].append(index.strftime('%Y-%m-%d'))
        echarts_data['Value'].append(row)
    
    # 返回转换后的数据给前端
    return echarts_data
