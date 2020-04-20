
path = document.getElementById("path").innerHTML;

function loadFile(filePath) {
  var result = null;
  var xmlhttp = new XMLHttpRequest();
  xmlhttp.open("GET", filePath, false);
  xmlhttp.send();
  if (xmlhttp.status==200) {
    result = xmlhttp.responseText;
  }
  return result;
}

    file = loadFile(path);
    arr = file.split('\n')
    value = [[]]
     for (i=0; i < arr.length; i++) {
           try {
           dict = JSON.parse(arr[i]);
           var k =0;
           for(key in dict){

                if(k>value.length-1) value.push([])
                value[k].push( Number(dict[key].value)/10 )
                k++;

           }
           } catch (SyntaxError) {}
    }

console.log(value.length)
    for(i=0; i<value.length; i++){

        name = document.getElementById('iname'+i).innerHTML

        var trace1 = {
            y: value[i],
            type: 'scatter',
            name: name
        };

        var data = [trace1];

        var layout = {
            title:name
        };

        var graphDiv =  Plotly.newPlot('graf'+ i, data, layout);

    }
