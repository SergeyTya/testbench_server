
function sum(a) {
    return a.reduce((acc, val) => acc + val)
}

function mean(a) {
    return sum(a) / a.length
}

function stddev(arr) {
    const arr_mean = mean(arr)
    const r = function(acc, val) {
        return acc + ((val - arr_mean) * (val - arr_mean))
    }
    return Math.sqrt(arr.reduce(r, 0.0) / arr.length)
}

function smoothed_z_score(y, params) { // peak detector
    var p = params || {}
    // init cooefficients
    const lag = p.lag || 5
    const threshold = p.threshold || 3.5
    const influence = p.influece || 0.5

    if(y === undefined || y.length < lag + 2) {
        throw ` ## y data array to short(${y.length}) for given lag of ${lag}`
    }
    //console.log(`lag, threshold, influence: ${lag}, ${threshold}, ${influence}`)

    // init variables
    var signals = Array(y.length).fill(0)
    var filteredY = y.slice(0)
    const lead_in = y.slice(0, lag)
//console.log("1: " + lead_in.toString())
    var avgFilter = []
    avgFilter[lag-1] = mean(lead_in)
    var stdFilter = []
    stdFilter[lag-1] = stddev(lead_in)
//console.log("2: " + stdFilter.toString())

    for(var i = lag; i < y.length; i++) {
        //console.log(`${y[i]}, ${avgFilter[i-1]}, ${threshold}, ${stdFilter[i-1]}`)
        if (Math.abs(y[i] - avgFilter[i-1]) > (threshold * stdFilter[i-1])) {
            if(y[i] > avgFilter[i-1]) {
                signals[i] = +1     // positive signal
            } else {
                signals[i] = -1     // negative signal
            }
            // make influence lower
            filteredY[i] = influence * y[i] + (1 - influence) * filteredY[i-1]
        } else {
            signals[i] = 0          // no signal
            filteredY[i] = y[i]
        }

        // adjust the filters
        const y_lag = filteredY.slice(i-lag, i)
        avgFilter[i] = mean(y_lag)
        stdFilter[i] = stddev(y_lag)
    }

    return signals
}

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
    time = []
     for (i=0; i < arr.length; i++) {
           try {
           dict = JSON.parse(arr[i]);
           var k =0;
           for(key in dict){
                if(key == "time") {
                    time.push(dict[key])
                    continue
                }
                if(k>value.length-1) value.push([])
                value[k].push( Number(dict[key].value)/10 )
                k++;

           }
           } catch (SyntaxError) {}
    }

    for(i=0; i<value.length; i++){

        name = document.getElementById('iname'+i).innerHTML

        var trace1 = {
            y: value[i],
            x: time,
            type: 'scatter',
            name: name
        };

        var data = [trace1];

        var samples = [ value[i] ]


        var layout = {
            title:name,
            xaxis: {
              type: 'date',
            },
            annotations: [],
        };


        try {
            samples.forEach(function(sample) {
            const peaks = smoothed_z_score(sample, {lag: 10}, {threshold: 1} , {influence: 10})
           // console.log(peaks.length + ": " + peaks.toString())

           for(j=0;j<peaks.length;j++){
                if(peaks[j] != 0){

                    pos =j/peaks.length;
                        var result = {
                    xref: 'paper',
                    x: pos,
                    y: value[i][j],
                    xanchor: 'right',
                    yanchor: 'middle',
                    text: 'peak' + value[i][j],
                    showarrow: false,
                    font: {
                        family: 'Arial',
                        size: 16,
                        color: 'black'
                        }
                    };
                    layout.annotations.push(result);
                  }
           }
                       })
            } catch(e) {
                console.log(e)
            }


        var graphDiv =  Plotly.newPlot('graf'+ i, data, layout);

    }
