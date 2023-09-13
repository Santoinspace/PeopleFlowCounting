import numpy as np
import pandas as pd
# import matplotlib.pyplot as plt

def generate_data(seed=0):

    # 设置随机种子以获得可重复的结果
    np.random.seed(seed)

    # 生成日期范围（假设数据从2022年1月1日开始，每天一个数据点）
    start_date = '2022-01-01'
    end_date = '2022-04-10'
    date_range = pd.date_range(start=start_date, end=end_date)

    # 生成随机数据模拟进入超市的人数
    # 在周末（周五和周六）人数较多，季节性变化
    num_samples = len(date_range)
    mean_persons = 100  # 平均每天进入超市的人数

    data = []
    for date in date_range:
        day_of_week = date.weekday()
        if day_of_week in [4, 5]:  # 周五和周六人数较多
            num_people = int(np.random.normal(loc=mean_persons + 20, scale=10))
        else:
            num_people = int(np.random.normal(loc=mean_persons - 20, scale=10))
        
        # 添加季节性效应
        if date.month in [3, 4]:  # 春季人数稍多
            num_people += int(np.random.normal(loc=10, scale=5))
        elif date.month in [6, 7, 8]:  # 夏季人数较少
            num_people -= int(np.random.normal(loc=10, scale=5))
        
        data.append([date, num_people])

    df = pd.DataFrame(data, columns=['Date', 'Value'])
    
    # 转换数据格式为适用于 ECharts 的形式
    
    # 日期格式转换
    echarts_data = {
        'Date': [],
        'Value': []
    }
    
    # 转换
    for index, row in df.iterrows():
        echarts_data['Date'].append(row['Date'].strftime('%Y-%m-%d'))
        echarts_data['Value'].append(row['Value'])

    # 返回转换后的数据给前端
    return echarts_data

# # 创建DataFrame
# df = pd.DataFrame(data, columns=['Date', 'PeopleCount'])

# # 可视化数据
# plt.figure(figsize=(12, 6))
# plt.plot(df['Date'], df['PeopleCount'])
# plt.xlabel('日期')
# plt.ylabel('人数')
# plt.title('模拟超市人流量')
# plt.grid(True)
# plt.tight_layout()
# plt.show()

# # 将数据保存到CSV文件中
# df.to_csv('supermarket_traffic_data.csv', index=False)
