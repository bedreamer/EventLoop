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
        max_zoom_in: 13,

        // 二值化白点
        bwhite: "#FFFFFF",
        // 二值化黑点
        bblack: "#777777",
        // 边界颜色
        edge_color: "#00FF00",
        // 二值化阈值
        threshold: 128,

        // 显示边界开关
        display_edge: false,
        // 显示模式, binary: 二值化图，gray: 灰度图，rgb: 真彩色
        display_mode: "binary",

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

        // 显示的最后一个帧
        last_frame: undefined,
    };

    // 获取到显示对象后需要重设一下显示区域的大小
    display_resize(ctx, ctx.device_width, ctx.device_height);

    $('#id_resolution').html(ctx.width + 'x' + ctx.height);
    $('#id_unit').html('x' + ctx.unit);
    return ctx;
}

// 重设显示区域大小
function display_resize(ctx, width, height) {
    ctx.canvas.width = ctx.device_width;
    ctx.canvas.height = ctx.device_height;
    $('.frame_border').css('width', (ctx.canvas.width + 10) + 'px');
}

// 显示区域放大
function display_zoom_in(ctx) {
    if ( ctx.unit < ctx.max_zoom_in ) {
        ctx.unit = ctx.unit + 1;
        ctx.device_width = ctx.width * ctx.unit;
        ctx.device_height = ctx.height * ctx.unit;
        display_resize(ctx, ctx.device_width, ctx.device_height);
        display_update(ctx);
    }
}

// 显示区域缩小
function display_zoom_out(ctx) {
    if ( ctx.unit > 1 ) {
        ctx.unit = ctx.unit - 1;
        ctx.device_width = ctx.width * ctx.unit;
        ctx.device_height = ctx.height * ctx.unit;
        display_resize(ctx, ctx.device_width, ctx.device_height);
        display_update(ctx);
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

// 更新显示帧
function display_update(ctx) {
    // 无数据，不处理。
    if ( ctx.last_frame == undefined ) {
        return;
    }

    if ( ctx.display_mode == 'binary' ) {
        var lines = ctx.last_frame.lines_pixels;
        for ( var i = 0; i < lines.length; i ++ ) {
            draw_logic_line_binary(ctx, i, lines[i].pixels, ctx.last_frame.edge_pixels[i]);
        }
        $('#id_frame_tsp').html(ctx.last_frame.tsp);
    } else if ( ctx.display_mode == 'gray' ) {
        var lines = ctx.last_frame.lines_pixels;
        for ( var i = 0; i < lines.length; i ++ ) {
            draw_logic_line_gray(ctx, i, lines[i].pixels, ctx.last_frame.edge_pixels[i]);
        }
        $('#id_frame_tsp').html(ctx.last_frame.tsp);
    } else if ( ctx.display_mode == 'rgb' ) {
    } else {
        // not supported.
    }
}

// 设置当前显示的帧
function display_set_frame(ctx, frame) {
    ctx.last_frame = frame;
}

// 获取当前显示的帧
function display_get_frame(ctx) {
    return ctx.frame;
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

// 在屏幕上输出逻辑点阵列-二值化
function draw_logic_line_binary(ctx, idx_line, points, edge_arr) {
    var i = 0;
    for (i = 0; i < points.length && i < ctx.width; i ++ ) {
        if ( points[i] > ctx.threshold ) {
            ctx.handle.fillStyle = ctx.bblack;
        } else {
            ctx.handle.fillStyle = ctx.bwhite;
            // 如果要显示边界就绘制
            if ( ctx.display_edge == true && edge_arr != undefined && edge_arr[i] > 0 ) {
                ctx.handle.fillStyle = ctx.edge_color;
            }
        }

        ctx.handle.fillRect(i * ctx.unit, idx_line * ctx.unit, ctx.unit, ctx.unit);
    }

    // 不足的地方用黑点补齐
    ctx.handle.fillStyle = ctx.bblack;
    for (; i < ctx.width; i ++ ) {
        ctx.handle.fillRect(i * ctx.unit, idx_line * ctx.unit, ctx.unit, ctx.unit);
    }
}

// 在屏幕上输出逻辑点阵列-灰度图
function draw_logic_line_gray(ctx, idx_line, points, edge_arr) {
    var i = 0;
    for (i = 0; i < points.length && i < ctx.width; i ++ ) {
        ctx.handle.fillStyle = "rgb("+ points[i] +"," + points[i] + ","+ points[i] +")";
        // 如果要显示边界就绘制
        if ( ctx.display_edge == true && edge_arr != undefined && edge_arr[i] > 0 ) {
            ctx.handle.fillStyle = ctx.edge_color;
        }

        ctx.handle.fillRect(i * ctx.unit, idx_line * ctx.unit, ctx.unit, ctx.unit);
    }

    // 不足的地方用黑点补齐
    ctx.handle.fillStyle = ctx.bblack;
    for (; i < ctx.width; i ++ ) {
        ctx.handle.fillRect(i * ctx.unit, idx_line * ctx.unit, ctx.unit, ctx.unit);
    }
}

var ctx = new_display("display", 120, 60, 6);
draw_welcome(ctx)


function getPointOnCanvas(canvas, x, y) {
    var bbox = canvas.getBoundingClientRect();
    return { x: Math.round(x - bbox.left * (canvas.width  / bbox.width)),
    y: Math.round(y - bbox.top  * (canvas.height / bbox.height))};
}

// 鼠标移动事件
function doMouseMove(event) {
    var x = event.pageX;
    var y = event.pageY;
    var canvas = event.target;
    var loc = getPointOnCanvas(ctx.canvas, x, y);
    var lx = Math.round(loc.x / ctx.unit);
    var ly = Math.round(loc.y / ctx.unit);
    if ( lx >= ctx.width || ly >= ctx.width ) {
        return;
    }
    $('#id_location').html("(" + lx + ',' + ly + ')');
    $('#id_line_tsp').html(ctx.last_frame.lines_pixels[ly].tsp);
}
ctx.canvas.addEventListener('mousemove', doMouseMove, false);

// 生成一个帧
function generate_frame(width, height) {
    var frame = new Array(height);
    var edge_mask = new Array(height);
    for ( var y = 0; y < height; y ++ ) {
        var arr = new Array(width);
        var edge_arr = new Array(width);
        for ( var n = 0; n < arr.length; n ++ ) {
            arr[n] = random(0, 255);
            edge_arr[n] = random(0, 2);
        }
        var dateObj = new Date();
        var datetime = dateObj.toLocaleDateString() + ' ' + dateObj.toLocaleTimeString();
        frame[y] = {
            pixels: arr,
            datetime: datetime,
            tsp: dateObj.valueOf()
        };

        edge_mask[y] = edge_arr;
    }
    var dateObj = new Date();
    var datetime = dateObj.toLocaleDateString() + ' ' + dateObj.toLocaleTimeString();

    var package = {
        lines_pixels: frame,
        edge_pixels: edge_mask,
        datetime: datetime,
        tsp: dateObj.valueOf()
    };

    return package;
}

var frame = generate_frame(120, 60);
console.log(frame);
display_set_frame(ctx, frame);
display_update(ctx);

$('#start').click(function(){
    console.log("start");
});

$('#stop').click(function(){
    console.log("stop");
});

$("#zoom_in").click(function(){
    display_zoom_in(ctx);
    $('#id_unit').html('x' + ctx.unit);
});

$("#zoom_out").click(function(){
    display_zoom_out(ctx);
    $('#id_unit').html('x' + ctx.unit);
});

$("#frame_pre").click(function(){
    var frame = generate_frame(120, 60);
    display_set_frame(ctx, frame);
    display_update(ctx);
});

$("#frame_next").click(function(){
    var frame = generate_frame(120, 60);
    display_set_frame(ctx, frame);
    display_update(ctx);
});

$("#edge").click(function(){
    if ( ctx.display_edge == false ) {
        ctx.display_edge = true;
        $("#edge").html("隐藏边界");
        display_update(ctx);
    } else {
        ctx.display_edge = false;
        $("#edge").html("显示边界");
        display_update(ctx);
    }
});

$("#binary").click(function(){
    ctx.display_mode = "binary";
    display_update(ctx);
    $("#id_mode").html("二值");
});

$("#gray").click(function(){
    ctx.display_mode = "gray";
    display_update(ctx);
    $("#id_mode").html("灰度");
});

$( "#slider" ).slider(
    {
        value: ctx.threshold,
        max: 255,
        range: "min",
        animate: true,
        change: function(event, ui) {
            console.log(ui.value);
        },
        slide: function(event, ui) {
            $('#id_thrhold').html(ui.value);
            ctx.threshold = ui.value;
            display_update(ctx);
        }
    }
);
$("#slider").css("width", "450px");
$('#id_thrhold').html(ctx.threshold);

var wifi_address = $.cookie('wifi');
if ( wifi_address != undefined ) {
    $('#id_addr').val(wifi_address);
}


var handle = undefined;
function pool_data() {
    var wifi = $('#id_addr').val();
    $.getJSON('http://127.0.0.1:8080/live.json?key=' + wifi + '&t=' + Date.parse(new Date()), '', function(data, status, xhr) {
        if ( data.status == 'ok' ) {
            pool_start(10);
        } else {
            disconnect(wifi);
            $('#id_msg').html(data.status);
        }
    }).fail(function(){
        disconnect(wifi);
        $('#id_msg').html('数据连接异常中止！');
    });
}

function pool_start(t) {
    if ( handle != undefined ) {
        clearTimeout(handle);
    }

    handle = setTimeout(pool_data(), t);
}

function pool_stop() {
    if ( handle != undefined ) {
        clearTimeout(handle);
    }
}

function connection(wifi) {
    $('#link').attr('disable', 'true');
    $.getJSON('http://127.0.0.1:8080/connect.json?addr=' + wifi + '&t=' + Date.parse(new Date()), '', function(data, status, xhr) {
        if ( data.status == 'ok') {
            $('#link').html('断开');
            $('#link').removeClass('btn-success');
            $('#link').addClass('btn-danger');
            $('#id_msg').html('&nbsp;');
            pool_start(100);
        } else {
            $('#id_msg').html(data.reason);
        }
        $('#link').attr('disable', 'false');
    }).fail(function(){
        $('#id_msg').html('无法连接！');
        $('#link').attr('disable', 'false');
    });
}

function disconnect(wifi) {
    $('#link').attr('disable', 'true');
    $.getJSON('http://127.0.0.1:8080/drop.json?key=' + wifi + '&t=' + Date.parse(new Date()), '', function(data, status, xhr) {
        if ( data.status == 'ok') {
            $('#id_msg').html('&nbsp;');
            $('#link').html('连接');
            $('#link').removeClass('btn-danger');
            $('#link').addClass('btn-success');
        } else {
            $('#id_msg').html(data.reason);
        }
        $('#link').attr('disable', 'false');
    }).fail(function(){
        $('#id_msg').html('无法连接！');
        $('#link').attr('disable', 'false');
    });
}

$('#link').click(function(){
    var wifi = $('#id_addr').val();
    if ( wifi != undefined && wifi != null && wifi != '' ) {
        $.cookie('wifi', wifi, { expires: 60});
    }
    var title = $('#link').html();
    if ( title == '连接') {
        $('#id_msg').html('&nbsp;');
        connection(wifi);
    } else {
        $('#id_msg').html('&nbsp;');
        disconnect(wifi);
    }

});
