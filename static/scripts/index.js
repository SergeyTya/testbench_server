
var socket = new WebSocket("ws://localhost:8080/ws");

socket.onopen = function(){
    console.log("connected");
};

function set_value_by_id(ID, value){
   tmp = document.getElementById(ID);
   if(tmp!=null)tmp.innerHTML=value
}

socket.onmessage = function (message) {
    let dict = JSON.parse(message.data);

    for (key in  dict) {
        if(key=="MPCH_saveToFile") {
            window.open('\save_mprm');
            continue
        }
         var tmp = document.getElementById(key);
         if(tmp!=null){
            tmp.innerHTML=dict[key].value;
            if ("color" in dict[key] ) tmp.style.background = dict[key].color
         }

         tmp = document.getElementsByName(key)[0];
         if(tmp!=null){
            tmp.value=dict[key].value;
            if ("color" in dict[key] ) tmp.style.background = dict[key].color
         }
    }
};

socket.onclose = function(){
    console.log("disconnected");
};

sendMessage = function(message) {
    console.log("sending: " + message);
    socket.send(message);
};
