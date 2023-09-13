import os
import time

from flask.json import jsonify
from AIDetector_pytorch import Detector
import cv2
import numpy as np
import flask
import threading

from predict.data import *
from predict.predict import *

last_timestamp = 0

def generate_id():
    global last_timestamp
    current_timestamp = int(time.time() * 1000)  # 获取当前时间戳，乘以1000转换为毫秒

    # 如果当前时间戳小于等于上一个生成的时间戳，增加1毫秒以确保唯一性
    if current_timestamp <= last_timestamp:
        current_timestamp = last_timestamp + 1

    last_timestamp = current_timestamp
    return current_timestamp

def processFile(src, dest, videoSize, poly_down, poly_up, poly_wait):

    name = 'demo'

    resource = src
    destination = dest

    # 根据视频尺寸，填充一个polygon，供撞线计算使用
    mask_image_temp = np.zeros(videoSize, dtype=np.uint8)

    # 初始化2个撞线polygon
    list_pts_blue = poly_down
    ndarray_pts_blue = np.array(list_pts_blue, np.int32)
    polygon_blue_value_1 = cv2.fillPoly(mask_image_temp, [ndarray_pts_blue], color=1)
    
    # print("polygon_blue_value_1的形状是:")
    # print(polygon_blue_value_1)
    
    polygon_blue_value_1 = polygon_blue_value_1[:, :, np.newaxis]
    # print(polygon_blue_value_1)
    # print("************")

    # 填充第二个polygon
    mask_image_temp = np.zeros(videoSize, dtype=np.uint8)
    list_pts_yellow = poly_up
    ndarray_pts_yellow = np.array(list_pts_yellow, np.int32)
    polygon_yellow_value_2 = cv2.fillPoly(mask_image_temp, [ndarray_pts_yellow], color=2)
    polygon_yellow_value_2 = polygon_yellow_value_2[:, :, np.newaxis]
    
    # 填充第三个polygon用作判断等待
    mask_image_temp = np.zeros(videoSize, dtype=np.uint8)
    list_pts_green = poly_wait
    ndarray_pts_green = np.array(list_pts_green, np.int32)
    polygon_green_value_3 = cv2.fillPoly(mask_image_temp, [ndarray_pts_green], color=3)
    polygon_green_value_3 = polygon_green_value_3[:, :, np.newaxis]

    # 撞线检测用mask，包含2个polygon，（值范围 0、1、2），供撞线计算使用
    polygon_mask_blue_and_yellow = polygon_blue_value_1 + polygon_yellow_value_2 + polygon_green_value_3

    # 缩小尺寸，1920x1080->960x540
    polygon_mask_blue_and_yellow = cv2.resize(polygon_mask_blue_and_yellow, (888, 500))

    # 蓝 色盘 b,g,r
    blue_color_plate = [255, 0, 0]
    # 蓝 polygon图片
    blue_image = np.array(polygon_blue_value_1 * blue_color_plate, np.uint8)

    # 黄 色盘
    yellow_color_plate = [0, 255, 255]
    # 黄 polygon图片
    yellow_image = np.array(polygon_yellow_value_2 * yellow_color_plate, np.uint8)
    
    # 绿 色盘
    green_color_plate = [0, 255, 0]
    # 绿 polygon图片
    green_image = np.array(polygon_green_value_3 * green_color_plate, np.uint8)

    # 彩色图片（值范围 0-255）
    color_polygons_image = blue_image + yellow_image +green_image
    # 缩小尺寸，1920x1080->960x540
    color_polygons_image = cv2.resize(color_polygons_image, (960, 540))

    # list 与蓝色polygon重叠
    list_overlapping_blue_polygon = []

    # list 与黄色polygon重叠
    list_overlapping_yellow_polygon = []
    
    # list 与绿色polygon重叠
    list_overlapping_green_polygon = []

    # 进入数量
    down_count = 0
    # 离开数量
    up_count = 0
    
    # 平均等待数量
    wait_count = 0
    # 总时间
    time = 0
    # 每个人等待的时间间隔列表
    wait_list = {}

    font_draw_number = cv2.FONT_HERSHEY_SIMPLEX
    draw_text_postion = (int(960 * 0.01), int(540 * 0.05))


    det = Detector()
    cap = cv2.VideoCapture(resource)
    #cap = cv2.VideoCapture(0)

    fps = int(cap.get(5))
    print('fps:', fps)
    t = int(1000/fps)

    videoWriter = None

    while True:

        # try:
        _, im = cap.read()
        
        if im is None:
            break
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        im = cv2.resize(im,(888,500))
        
        # 总的时间加一
        time += 1
        

        result = det.feedCap(im)
        resultfrm = result['frame']
        list_bboxs = result['bboxes']
        

        #resultfrm = imutils.resize(resultfrm,width=888, height=500)
        resultfrm = cv2.resize(resultfrm,(888,500))
        #(h,w) = resultfrm.shape[:2]
        #print(h,w)
        #color_polygons_image = imutils.resize(color_polygons_image,width=888, height=500)
        color_polygons_image = cv2.resize(color_polygons_image,(888,500))
        #(h,w) = resultfrm.shape[:2]
        #print(h,w)


# 在这里面添加判断等待的代码
        if len(list_bboxs) > 0:
            # ----------------------判断撞线----------------------
            for item_bbox in list_bboxs:
                x1, y1, x2, y2, label, track_id = item_bbox

                # 撞线检测点，(x1，y1)，y方向偏移比例 0.0~1.0
                y1_offset = int(y1 + ((y2 - y1) * 0.6))

                # 撞线的点
                y = y1_offset
                x = x1

                if polygon_mask_blue_and_yellow[y, x] == 1:
                    # 如果撞 蓝polygon
                    if track_id not in list_overlapping_blue_polygon:
                        list_overlapping_blue_polygon.append(track_id)
                    pass

                    # 判断 黄polygon list 里是否有此 track_id
                    # 有此 track_id，则 认为是 外出方向
                    if track_id in list_overlapping_yellow_polygon:
                        # 外出+1
                        up_count += 1

                        print(
                            f'类别: {label} | id: {track_id} | 上行撞线 | 上行撞线总数: {up_count} | 上行id列表: {list_overlapping_yellow_polygon}')

                        # 删除 黄polygon list 中的此id
                        list_overlapping_yellow_polygon.remove(track_id)

                        pass
                    else:
                        # 无此 track_id，不做其他操作
                        pass

                elif polygon_mask_blue_and_yellow[y, x] == 2:
                    # 如果撞 黄polygon
                    if track_id not in list_overlapping_yellow_polygon:
                        list_overlapping_yellow_polygon.append(track_id)
                    pass

                    # 判断 蓝polygon list 里是否有此 track_id
                    # 有此 track_id，则 认为是 进入方向
                    if track_id in list_overlapping_blue_polygon:
                        # 进入+1
                        down_count += 1

                        print(
                            f'类别: {label} | id: {track_id} | 下行撞线 | 下行撞线总数: {down_count} | 下行id列表: {list_overlapping_blue_polygon}')

                        # 删除 蓝polygon list 中的此id
                        list_overlapping_blue_polygon.remove(track_id)

                        pass
                    else:
                        # 无此 track_id，不做其他操作
                        pass
                    pass
                
                elif polygon_mask_blue_and_yellow[y, x] == 3:
                    
                    # 如果此前已经在等待区域
                    if track_id in wait_list:
                        wait_list[track_id] = wait_list.get(track_id) + 1
                    # 如何是首次进入等待区域
                    else:
                        wait_list[track_id] = 1
                        
                else:
                    pass
                pass

            pass

            # ----------------------清除无用id----------------------
            list_overlapping_all = list_overlapping_yellow_polygon + list_overlapping_blue_polygon
            for id1 in list_overlapping_all:
                is_found = False
                for _, _, _, _, _, bbox_id in list_bboxs:
                    if bbox_id == id1:
                        is_found = True
                        break
                    pass
                pass

                if not is_found:
                    # 如果没找到，删除id
                    if id1 in list_overlapping_yellow_polygon:
                        list_overlapping_yellow_polygon.remove(id1)
                    pass
                    if id1 in list_overlapping_blue_polygon:
                        list_overlapping_blue_polygon.remove(id1)
                    pass
                pass
            list_overlapping_all.clear()
            pass

            # 清空list
            list_bboxs.clear()

            pass
        
        
        
        else:
            # 如果图像中没有任何的bbox，则清空list
            list_overlapping_blue_polygon.clear()
            list_overlapping_yellow_polygon.clear()
            pass
        pass

        wait_count = sum(wait_list.values())/time
        wait_count = round(wait_count,3)
        
        text_draw = 'DOWN: ' + str(down_count) + \
                    ' , UP: ' + str(up_count) + \
                    ' , AvgWait' + str(wait_count)
                    
        resultfrm = cv2.putText(img=resultfrm, text=text_draw,
                                         org=draw_text_postion,
                                         fontFace=font_draw_number,
                                         fontScale=1, color=(10, 230, 150), thickness=2)
        
        resultfrm = cv2.add(resultfrm, color_polygons_image)
        if videoWriter is None:
            fourcc = cv2.VideoWriter_fourcc(
                'm', 'p', '4', 'v')  # opencv3.0
            videoWriter = cv2.VideoWriter(
                destination, fourcc, fps, (resultfrm.shape[1], resultfrm.shape[0]))

        #print(result)
        videoWriter.write(resultfrm)
        cv2.imshow(name, resultfrm)
        cv2.waitKey(t)

        if cv2.getWindowProperty(name, cv2.WND_PROP_AUTOSIZE) < 1:
            # 点x退出
            break
        # except Exception as e:
        #     print(e)
        #     break

    cap.release()
    videoWriter.release()
    cv2.destroyAllWindows()

    doneFlag(dest)

def doneFlag(dest):
    # 给目标文件名加上done标签
    os.rename(dest, dest.split('.')[0] + '_done.mp4')

def checkFlag(id):
    # 检查目标文件名是否有done标签
    id = "out/" + id + '_out_done.mp4'
    return os.path.exists(id)


# if __name__ == '__main__':
#     process('./testVedios/test1.mp4', 'test_out.mp4', (1080, 1920), 
#             [[200, 500], [1800, 500], [1800, 530], [200, 530]], 
#             [[200, 530], [1800, 530],  [1800, 560], [200, 560]])

# flask主程序
app = flask.Flask(__name__, template_folder='./', static_folder='static')

# 根路由 index.html
@app.route('/', methods=['GET', 'POST'])
def index():
        return flask.render_template('index.html')


# 分析页
@app.route('/analysis', methods=['GET', 'POST'])
def analysis():
        return flask.render_template('analysis.html')

# 生成模拟数据
@app.route('/generateData', methods=['GET', 'POST'])
def generate_simudata():
    # 系统时间种子
    seed = int(time.time())
    data = generate_data(seed)
    return jsonify(data)

@app.route('/predict', methods=['POST'])
def predit_future():
    data = flask.request.get_json()
    future_steps = int(data['future_steps'])
    dates = data['Date']
    values = data['Value']
    # 转换为pandas的DataFrame
    df = pd.DataFrame({'Date': dates, 'Value': values})
    # 转换为pandas的时间序列
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)
    return jsonify(predict(df, future_steps))


@app.route('/result', methods=['GET'])
def download_file():
    request_id = flask.request.args.get('request_id')
    print("request at", request_id)
    if checkFlag(request_id):
        filename = request_id + '_out_done.mp4'
        return flask.send_from_directory('out', filename, as_attachment=True, mimetype='video/mp4')

    # 如果请求编号无效或文件不存在，返回错误信息
    return jsonify({'error': '你所查询的报告未就绪或id错误'}), 404


# $.ajax({
#         url: "/process",
#         type: "POST",
#         data: JSON.stringify(data),
#         contentType: "application/json",
#         success: function (res) {
#             console.log(res);
#             alert("上传成功");
#         }
#     });
@app.route('/process', methods=['POST'])
def process():
    data = flask.request.get_json()
    src = 'files/' + data['videoName']
    # 生成唯一id
    id = generate_id()
    dest = 'out/' + str(id) + '_out.mp4'
    videoSize = (int(data['videoHeight']), int(data['videoWidth']))
    poly_down = data['down']
    poly_up = data['up']
    poly_wait = data['wait']
    print(src, dest, videoSize, poly_down, poly_up, poly_wait)
    # 新建线程完成process
    t = threading.Thread(target=processFile, args=(src, dest, videoSize, poly_down, poly_up, poly_wait))
    t.start()
    # 返回成功标签和id
    return {'status': 'success', 'id': id}

@app.route('/upload', methods=['POST'])
def upload():
    file = flask.request.files['file']
    print(file)
    # 保存到files
    file.save('files/' + file.filename)
    return 'success'

if __name__ == '__main__':
    app.run()

