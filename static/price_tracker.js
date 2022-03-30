const CHART_BACKGROUND_COLOR = 'rgb(255, 99, 132)';
const CHART_BORDER_COLOR = 'rgb(255, 99, 132)';
const MAX_PRICE_DEEP = 10;

let priceChart = undefined;

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
  var priceSocket = new WebSocket("ws://" + location.hostname + ":" + location.port + "/track-price");
  
  priceSocket.onmessage = function(event) {
      let tickerData = JSON.parse(event.data);
      if (priceChart.data.labels.length > MAX_PRICE_DEEP)
        removeData(priceChart);
      addData(priceChart, tickerData.updated, tickerData.price);
  };
  
  setInterval(function() {
    var tickerSelector = document.getElementById("ticker")
    priceSocket.send(tickerSelector.value)
  }, 1000);
}

function onTickerSelect() {
  var ticker = document.getElementById("ticker").value;

  $.ajax('/ticker-price', {
    type: 'get',
    data: $.param({'ticker_name': ticker}),
    success: onTickerPriceReceive,
  });
}

function onTickerPriceReceive(response) {
  var labels = [];
  var prices = [];
  response.forEach(pair => {
    labels.push(pair[0]);
    prices.push(pair[1]);
  });

  const data = {
    labels: labels,
    datasets: [{
      label: 'Ticker price',
      backgroundColor: CHART_BACKGROUND_COLOR,
      borderColor: CHART_BORDER_COLOR,
      data: prices,
    }],
  };
  const config = {
    type: 'line',
    data: data,
    options: {},
  };

  canvas = document.getElementById('ticker-chart');
  if (priceChart !== undefined)
    priceChart.destroy();
  
  priceChart = new Chart(canvas, config);
}

$(document).ready(function() {
  $('.select-ticker').select2();
  onTickerSelect();
  initSocket();
  $(".select-ticker").on("select2:select", function (e) { onTickerSelect(); });
});
