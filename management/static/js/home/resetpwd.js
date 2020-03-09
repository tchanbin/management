//提交成功提示框

// $(document).ready(function () {
$._messengerDefaults = {
    extraClasses: 'messenger-fixed messenger-theme-future messenger-on-top '
}
    if ("{{ message }}" == "ok") {
        $.globalMessenger().post({
            message: "操作成功",//提示信息
            type: 'info',//消息类型。error、info、success
            hideAfter: 3,//多长时间消失
            showCloseButton: true,//是否显示关闭按钮
            hideOnNavigate: true //是否隐藏导航
        });
    } else if ("{{ message }}" == "nok") {
        alert("操作失败")
    }
// });
alert("好")