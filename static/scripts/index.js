
//var socket = new WebSocket("ws://192.168.1.248:8080/ws");
//var socket = new WebSocket("ws://192.168.1.196:8080/ws"); // PiOne wifi
//var socket = new WebSocket("ws://localhost:8080/ws");
var socket = new WebSocket("ws://192.168.178.138:8080/ws"); //WM

socket.onopen = function(){
    console.log("connected");
};

function set_value_by_id(ID, value , color){
   tmp = document.getElementById(ID);
   if(tmp!=null)tmp.innerHTML=value
   if(color!=null) tmp.style.background = color
}

function set_value_by_name(name, value , color){
   tmp = document.getElementsByName(name);
   if(tmp!=null){
            for (el in tmp){
                el.value=value
                if(color!=null)  el.style.background = color
            }
   }
}

var indi_counter=0;
var bconsol_count = 0;

socket.onmessage = function (message) {

    console.log(message)

    let dict
    try {
        dict = JSON.parse(message.data);
    } catch (SyntaxError) {
        console.log(message.data)
        return
    }

    for (key in  dict) {

        //console.log(dict[key])

        if(key== "bconsol"){
            tmp = document.getElementById(key);
            tmp.innerHTML=dict[key].value+'<br>'+tmp.innerHTML;
            continue
        }else{
            bconsol_count = 0;
        }

        if(key=="MPCH_saveToFile") {
            window.open('\save_mprm');
            continue
        }

        if(key=="MPCH_mes"){
            console.log(dict[key].value)
            continue
        }
         var tmp = document.getElementById(key);

         // schneider range change by indicator color
         if(key == "SchnI3"| key == "SchnI4" | key == "SchnI5"){
                tmp = document.getElementById(key);
                if(tmp.style.background == "blue") continue;
                if(tmp.style.background == "red"){
                if(Number(tmp.innerHTML) == dict[key].value){tmp.style.background = "green";}else{}
                continue;
            }

         }

         if(tmp!=null){
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
            if(key == 'MPCH_ireg0') {
                var hex = Number(dict[key].value).toString(16)
                set_value_by_id("plotlyIndi0", "0x0" +  hex)
            }else{
                set_value_by_id("plotlyIndi"+key.slice(9,10), Number(dict[key].value)/10)
            }
          }

//         if(key == "MPCH_hreg4"){
//            tmp = document.getElementById('CDirIndi');
//            if(dict[key].value == "0") tmp.value = "Вперед";
//            if(dict[key].value == "1") tmp.value = "Назад" ;
//         }

//          if(key == "MPCH_hreg5"){
//            tmp = document.getElementById('MPCH_FreqCntrl');
//            tmp.max = dict[key];
//         }

        if(key == "MPCH_hreg3"){
                tmp = document.getElementById('MPCH_FRI');
                if(tmp.style.background == "blue" | tmp.style.background == "green" ) continue;
                if(tmp.style.background == "red"){
                    if(Number(tmp.innerHTML*10) == dict[key].value){tmp.style.background = "green";}
                    continue;
                }
                tmp.innerHTML = (dict[key].value * 0.1).toFixed(1)
        }

        if(key == "MPCH_hreg4"){
            tmp = document.getElementById('MPCH_FDI');
            if(tmp.style.background == "blue" | tmp.style.background == "green" ) continue;
            if(tmp.style.background == "red"){
                    if(tmp.innerHTML == "Прямое" & dict[key].value==0){tmp.style.background = "green";}
                    if(tmp.innerHTML == "Обратное" & dict[key].value==1){tmp.style.background = "green";}
                    continue;
            }
            if(dict[key].value==0) tmp.innerHTML = "Прямое";
            if(dict[key].value==1) tmp.innerHTML = "Обратное";
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

