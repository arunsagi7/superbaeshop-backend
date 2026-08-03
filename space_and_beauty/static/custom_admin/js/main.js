
function comfirmModel(type, id) {
    var model = $('#ProfileModal');
    var model_text = "";
    var confirm_action_url = "";
    switch (type) {
        case 1:
            model_text = `Really Do You want Really move cod`;
            model = $('#ProfileModal');
            confirm_action_url = `move_order_cod/${id}/`;
            break;

           case 2:
            model_text = `Really Do You want Really Success Payment`;
            model = $('#moveOnlinePayment');
            confirm_action_url = `move_order_payment/${id}/`;
            break;
             case 3:
            model_text = `Really Do You want Really Cancel the Order`;
            model = $('#ProfileModal');
            confirm_action_url = `cancel_order/${id}/`;
            break;

        default:
            model_text = "Really Do You complete this action";
            confirm_action_url = "/";
            break;
    }

    model.modal('show');
    if (type==2){
        $('#online_pay_move_order_id').attr("action", confirm_action_url);
    }else{
        $('#move_order_id').attr("action", confirm_action_url);
    }
    $('#model-text').text(model_text)


}