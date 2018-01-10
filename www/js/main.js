function random(min,max){
    return Math.floor(min+Math.random()*(max-min));
}
///////////////////////////////////////////////////////

// 新建一个显示canvas
function new_display(id, width, height, unit) {
    var context = document.getElementById(id).getContext("2d");
    var ctx = {
        // 逻辑宽度
        width: width,
        // 逻辑高度
        height: height,
        // 设备宽度实际像素数
        device_width: width * unit,
        // 设备高度实际像素数
        device_height: height * unit,
        // 设备像素宽度比值/逻辑宽度
        unit: unit,
        // html标签ID号
        id: id,
        // 设备句柄
        handle: context,
        // canvas 对象
        canvas: context.canvas,

        // 默认清屏颜色
        default_clear_color: "#000000",

        // 最大支持放大倍数
        max_zoom_in: 10,

        // 二值化白点
        bwhite: "#FFFFFF",
        // 二值化黑点
        bblack: "#777777",

        // datetime文本大小, 单位: px
        datetime_font_size: 16,
        // datetime文本颜色
        datetime_font_color: "#FFFFFF",

        // welcome文本内容
        welcome_txt: "正在连接设备...",
        // welcome文本大小, 单位: px
        welcome_font_size: 24,
        // welcome文本颜色
        welcome_font_color: "#FFFFFF",

        // offline文本内容
        offline_txt: "无信号",
        // offline文本大小, 单位: px
        offline_font_size: 24,
        // offline文本颜色
        offline_font_color: "#FFFFFF",
    };

    // 获取到显示对象后需要重设一下显示区域的大小
    display_resize(ctx, ctx.device_width, ctx.device_height);
    return ctx;
}

// 重设显示区域大小
function display_resize(ctx, width, height) {
    ctx.canvas.width = ctx.device_width;
    ctx.canvas.height = ctx.device_height;
}

// 显示区域放大
function display_zoom_in(ctx) {
    if ( ctx.unit < ctx.max_zoom_in ) {
        ctx.unit = ctx.unit + 1;
        ctx.device_width = ctx.width * ctx.unit;
        ctx.device_height = ctx.height * ctx.unit;
        display_resize(ctx, ctx.device_width, ctx.device_height);
    }
}

// 显示区域缩小
function display_zoom_out(ctx) {
    if ( ctx.unit > 1 ) {
        ctx.unit = ctx.unit - 1;
        ctx.device_width = ctx.width * ctx.unit;
        ctx.device_height = ctx.height * ctx.unit;
        display_resize(ctx, ctx.device_width, ctx.device_height);
    }
}

// 清空屏幕
function display_clean(ctx, color) {
    if ( color == undefined ) {
        color = ctx.default_clear_color;
    }
    ctx.handle.fillStyle = color;
    ctx.handle.fillRect(0, 0, ctx.device_width, ctx.device_height);
}

// 在指定位置使用指定颜色输出字符串
function draw_text(ctx, txt, color, x, y) {
    ctx.handle.fillStyle = color;
    ctx.handle.fillText(txt, x, y);
}

// 在给定y轴处居中输出字符串
function draw_x_center_text(ctx, txt, color, y, font_size) {
    ctx.handle.font = font_size + 'px serif';
    var x = ctx.device_width / 2 - ctx.handle.measureText(txt).width / 2;
    draw_text(ctx, txt, color, x, y);
}

// 在给定x轴处居中输出字符串
function draw_y_center_text(ctx, txt, color, x, font_size) {
    var y = ctx.device_height / 2 - font_size / 2;
    draw_text(ctx, txt, color, x, y);
}

// 屏幕居中输出字符串
function draw_center_text(ctx, txt, color, font_size) {
    ctx.handle.font = font_size + 'px serif';
    var x = ctx.device_width / 2 - ctx.handle.measureText(txt).width / 2;
    var y = ctx.device_height / 2 - font_size / 2;
    draw_text(ctx, txt, color, x, y);
}

// 在屏幕上输出当前日期和时间
function draw_datetime(ctx) {
    var dateObj = new Date();
    var datetime = dateObj.toLocaleDateString() + ' ' + dateObj.toLocaleTimeString();
    draw_x_center_text(ctx, datetime, ctx.datetime_font_color, 20, ctx.datetime_font_size);
}

// 在屏幕上输出欢迎信息
function draw_welcome(ctx, txt) {
    if ( txt == undefined ) {
        txt = ctx.welcome_txt;
    }
    display_clean(ctx);
    draw_datetime(ctx);
    draw_center_text(ctx, txt, ctx.welcome_font_color, ctx.welcome_font_size);
}

// 在屏幕上输出无信号信息
function draw_offline(ctx, txt) {
    if ( txt == undefined ) {
        txt = ctx.offline_txt;
    }
    display_clean(ctx);
    draw_datetime(ctx);
    draw_center_text(ctx, txt, ctx.offline_font_color, ctx.offline_font_size);
}

// 在屏幕上输出逻辑点阵列
function draw_logic_line(ctx, idx_line, points) {
    var i = 0;
    for (i = 0; i < points.length && i < ctx.width; i ++ ) {
        if ( points[i] > 0 ) {
            ctx.handle.fillStyle = ctx.bwhite;
        } else {
            ctx.handle.fillStyle = ctx.bblack;
        }
        ctx.handle.fillRect(i * ctx.unit, idx_line * ctx.unit, ctx.unit, ctx.unit);
    }

    // 不足的地方用黑点补齐
    ctx.handle.fillStyle = ctx.bblack;
    for (; i < ctx.width; i ++ ) {
        ctx.handle.fillRect(i * ctx.unit, idx_line * ctx.unit, ctx.unit, ctx.unit);
    }
}

var ctx = new_display("display", 120, 60, 5);
draw_welcome(ctx)

var hd = undefined;
var loop = 0;
function draw(){
    clearTimeout(hd);
    for ( var i = 10; i < 60; i ++ ) {
        var arr = new Array(120);
        for ( var n = 0; n < arr.length; n ++ ) {
            arr[n] = random(-100, 100);
        }
        draw_logic_line(ctx, i, arr);
    }
    hd = setTimeout(draw, 1000/24);
}

$('#start').click(function(){
    hd = setTimeout(draw, 1000/24);
    console.log("start");
});

$('#stop').click(function(){
    clearTimeout(hd);
    console.log("stop");
});

$("#zoom_in").click(function(){
    display_zoom_in(ctx);
});

$("#zoom_out").click(function(){
    display_zoom_out(ctx);
});
