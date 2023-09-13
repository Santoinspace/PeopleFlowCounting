let imageURL;
let instance;
let option = [];

const UP = 0,
    DOWN = 1,
    WAIT = 2,
    RECT = 1,
    POLY = 2;
let curDirection = DOWN;
let curShape = RECT;
let shapes = [{}, {}, {}];
let shapeType = [0, 0, 0];
let curVideo;

// instance = new CanvasSelect(".editContainer");

function initVideo(vid) {
    curVideo = vid;
}

function initImage(url) {
    imageURL = url;
}

function initInstance() {
    if (!imageURL)
        return;
    instance = new CanvasSelect(".editContainer", imageURL);
    instance.labelMaxLen = 10;
    instance.setData(option);
    // 图片加载完成
    instance.on("load", src => {
        console.log("image loaded", src);
    });
    // 添加
    instance.on("add", info => {
        console.log("add", info);
        // info.label = curDirection === UP ? "上行" : "下行";
        // info.fillStyle = curDirection === UP ? "rgba(255, 255, 0, 0.5)" : "rgba(0, 0, 255, 0.5)";

        // 三种情况
        // 上行（黄色） 下行（蓝色） 等待（绿色）
        switch (curDirection) {
            case UP:
                info.label = "上行";
                info.fillStyle = "rgba(255, 255, 0, 0.5)";
                break;
            case DOWN:
                info.label = "下行";
                info.fillStyle = "rgba(0, 0, 255, 0.5)";
                break;
            case WAIT:
                info.label = "等待";
                info.fillStyle = "rgba(0, 255, 0, 0.5)";
                break;
        }

        window.info = info;
        instance.update();
        // 结束绘制模式 
        change(0);
        shapes[curDirection] = info;
        shapeType[curDirection] = curShape;
    });
    // 删除
    instance.on("delete", info => {
        console.log("delete", info);
        window.info = info;
        // shapes[info.label === "上行" ? UP : DOWN] = {};
        let opDirection = info.label === "上行" ? UP : info.label === "下行" ? DOWN : WAIT;
        shapes[opDirection] = {};
    });
    // 选中
    instance.on("select", shape => {
        console.log("select", shape);
        window.shape = shape;
    });
    instance.on("updated", result => {});
}

function change(num) {
    instance.createType = num;
}

function zoom(type) {
    instance.setScale(type);
}

function fitting() {
    instance.fitZoom();
}

function changeData() {
    // const data = JSON.parse(output.value);
    instance.setData(data);
}

function onFocus() {
    instance.setFocusMode(!instance.focusMode);
}

function createShape() {
    // 先判断是否已经存在形状
    if (shapes[curDirection].index !== undefined)
        return;
    console.log("exists", shapes[curDirection].index);
    change(curShape);
}

function deleteShape() {
    let index = shapes[curDirection].index;
    if (index === undefined)
        return;
    instance.deleteByIndex(index);
}

function areaChange(type) {
    curDirection = type;
}

function shapeModeChange(type) {
    curShape = type;
}

function convertRectToPoly(rect) {
    // rect形如[[1,1], [2,2]]
    // 将对角线的两个点转化为四个顶点
    let x1 = rect[0][0],
        y1 = rect[0][1],
        x2 = rect[1][0],
        y2 = rect[1][1];
    return [
        [x1, y1],
        [x2, y1],
        [x2, y2],
        [x1, y2]
    ];
}

function upload() {
    // 先检测下行上行有没有都画了
    if (shapes[UP].index === undefined || shapes[DOWN].index === undefined || shapes[WAIT].index === undefined) {
        alert("请先画出所有标识区域");
        return;
    }
    // 消息框询问是否上传
    if (!confirm("是否上传？"))
        return;
    // 上传
    // 首先转换多边形数据 对于rect要转换成四个顶点
    let up = shapes[UP].coor,
        down = shapes[DOWN].coor,
        wait = shapes[WAIT].coor;
    if (shapeType[UP] === RECT)
        up = convertRectToPoly(up);
    if (shapeType[DOWN] === RECT)
        down = convertRectToPoly(down);
    if (shapeType[WAIT] === RECT)
        wait = convertRectToPoly(wait);
    let videoName = curVideo.getAttribute("data-name");
    let data = {
        videoName,
        videoHeight: curVideo.videoHeight,
        videoWidth: curVideo.videoWidth,
        up,
        down,
        wait
    };
    console.log(data);
    // 发送数据
    $.ajax({
        url: "/process",
        type: "POST",
        data: JSON.stringify(data),
        contentType: "application/json",
        dataType: "json",
        success: function (res) {
            console.log(res);
            inform(res.id);
        }
    });

}


let informLabel;

function inform(id) {
    $('#inform').show();
    $('#inform').text("请持请求编号回到主页面查询结果：" + id);
}