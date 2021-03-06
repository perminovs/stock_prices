const CHART_BACKGROUND_COLOR = 'rgb(255, 99, 132)';
const CHART_BORDER_COLOR = 'rgb(255, 99, 132)';
const MAX_PRICE_DEEP = undefined;

let priceChart = undefined;
let priceSocket = undefined;

function addData(chart, label, data) {
  chart.data.labels.push(label);
  chart.data.datasets.forEach((dataset) => {
      dataset.data.push(data);
  });
  chart.update();
}

function removeData(chart) {
  chart.data.labels.shift();
  chart.data.datasets.forEach((dataset) => {
      dataset.data.shift();
  });
  chart.update();
}

function initSocket() {
  priceSocket = new WebSocket("ws://" + location.hostname + ":" + location.port + "/track-price");
  
  priceSocket.onopen = function() {
      let tickerSelector = document.getElementById("ticker")
      let tickerName = tickerSelector.value;
      priceSocket.send(tickerName);
  }

  priceSocket.onmessage = function(event) {
      let tickerData = JSON.parse(event.data);

      let time = new Date(tickerData.created_at);
      addData(priceChart, time, tickerData.price);

      while (MAX_PRICE_DEEP && priceChart.data.labels.length > MAX_PRICE_DEEP)
        removeData(priceChart);
  };
}

function onTickerSelect() {
  let ticker_name = document.getElementById("ticker").value;

  if (priceSocket)
    priceSocket.close();

  $.ajax('/ticker-price', {
    type: 'get',
    data: $.param({'ticker_name': ticker_name}),
    success: onTickerPriceReceive,
  });
}

function onTickerPriceReceive(response) {
  let labels = [];
  let prices = [];
  response.forEach(item => {
    let time = new Date(item.created_at);
    labels.push(time);
    prices.push(item.price);
  });

  let ticker_name = document.getElementById("ticker").value;

  const data = {
    labels: labels,
    datasets: [{
      label: ticker_name,
      backgroundColor: CHART_BACKGROUND_COLOR,
      borderColor: CHART_BORDER_COLOR,
      data: prices,
    }],
  };
  const config = {
    type: 'line',
    data: data,
    options: {
      scales: {
        x: {
          type: 'time',
          ticks: {
            source: 'data',
          },
          title: {
            display: true,
            text: 'Time'
          }
        },
        y: {
          title: {
            display: true,
            text: 'Price'
          }
        },
      }
    },
  };

  canvas = document.getElementById('ticker-chart');
  if (priceChart !== undefined)
    priceChart.destroy();
  
  priceChart = new Chart(canvas, config);

  initSocket();
}

$(document).ready(function() {
  $('.select-ticker').select2();
  onTickerSelect();
  $(".select-ticker").on("select2:select", function (e) { onTickerSelect(); });
});
