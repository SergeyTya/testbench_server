
//var socket = new WebSocket("ws://192.168.1.248:8080/ws");
//var socket = new WebSocket("ws://192.168.1.196:8080/ws");
//var socket = new WebSocket("ws://localhost:8080/ws");
var socket = new WebSocket("ws://192.168.178.133:8080/ws");

socket.onopen = function(){
    console.log("connected");
};

function set_value_by_id(ID, value , color){
   tmp = document.getElementById(ID);
   if(tmp!=null)tmp.innerHTML=value
   if(color!=null) tmp.style.background = color
}

var indi_counter=0;

socket.onmessage = function (message) {

    let dict
    try {
        dict = JSON.parse(message.data);
    } catch (SyntaxError) {
        console.log(message.data)
        return
    }

    for (key in  dict) {

        //console.log(dict[key])

        if(key=="MPCH_saveToFile") {
            window.open('\save_mprm');
            continue
        }

        if(key=="MPCH_mes"){
            console.log(dict[key].value)
            continue
        }
         var tmp = document.getElementById(key);


         if(key == "SchnI3"| key == "SchnI4" | key == "SchnI5"){
            tmp = document.getElementById(key);
            if(tmp.style.background == "blue") continue;
            if(tmp.style.background == "red"){
                if(tmp.innerHTML == dict[key].value)tmp.style.background = "green";
                continue;
            }
         }

         if(tmp!=null){ // schneider range change by indicator color
            tmp.innerHTML=dict[key].value;
            if(key=="MPCH_Status"){
                if ("color" in dict[key] ) tmp.style.color = dict[key].color
            }else{
                if ("color" in dict[key] ) tmp.style.background = dict[key].color
            }
         }

         tmp = document.getElementsByName(key)[0];
         if(tmp!=null){
            tmp.value=dict[key].value;
            if ("color" in dict[key] ) tmp.style.background = dict[key].color
         }

         if(key.slice(0,9) == "MPCH_ireg"){
            set_value_by_id("plotlyIndi"+key.slice(9,10), Number(dict[key].value)/10)
          }

         if(key == "MPCH_hreg4"){
            tmp = document.getElementById('CDirIndi');
            if(dict[key].value == "0") tmp.value = "Вперед";
            if(dict[key].value == "1") tmp.value = "Назад" ;
         }

        if(key == "MPCH_hreg3"){
            var tmp = document.getElementById('CFreqDigit');
            tmp.value = dict[key].value/10;
            var val = document.getElementsByName('MPCH_hreg5')[0].value;
            if(val==null) return;
            tmp = document.getElementById('CFreqRange');
            tmp.value =(dict[key].value*1000/val).toFixed(0);
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

sendCommand = function(cmd, adr=0, value=0) {
    sendMessage('{"CMD":"'+cmd+'", "ADR":"'+adr+'", "VL":"'+value+'"}')
};
