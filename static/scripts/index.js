
var socket = new WebSocket("ws://localhost:8080/ws");

for (i=0; i <6; i++) {
    name = document.getElementById('iname'+i).innerHTML
    var graphDiv =  Plotly.newPlot(
        'plotlyIndi'+i,
        data = [{
            domain: { x: [0, 1], y: [0, 1] },
            value: 0.0,
            valueformat: "0.0f",
            title: {
                font: {size:18, color: '#F4E623'},
                text: name,
                opacity: 1
                },
            type: "indicator",
            mode: "number",
            gauge: { axis: { range: [null, 1000] } },
            delta: { reference: 0, valueformat: '.0f' },
            number: {valueformat: '0.1f'}
        }],
        layout = {
            font:{color:"#F97405"},
            paper_bgcolor: "#272C2F",
            autosize: "true",
            width: 240,
            height: 120,
            margin: {l:0,r:0,t:35,b:0,pad:0}
        }
    );
}

socket.onopen = function(){
    console.log("connected");
};

function set_value_by_id(ID, value){
   tmp = document.getElementById(ID);
   if(tmp!=null)tmp.innerHTML=value
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
        if(key=="MPCH_saveToFile") {
            window.open('\save_mprm');
            continue
        }

        if(key=="MPCH_mes"){
            console.log(dict[key].value)
            continue
        }
         var tmp = document.getElementById(key);

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
             Plotly.update("plotlyIndi"+key.slice(9,10), {value : Number(dict[key].value)/10}, {});
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
