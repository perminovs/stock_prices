const CHART_BACKGROUND_COLOR = 'rgb(255, 99, 132)';
const CHART_BORDER_COLOR = 'rgb(255, 99, 132)';
const MAX_PRICE_DEEP = 15;  // todo here or back-end?

let priceChart = undefined;
let lastUpdated = null;
let isSockerInitialized = false;

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

      tickerData.forEach(item => {
        if (item.created_at === lastUpdated)
          return;

        let time = new Date(item.created_at).toLocaleTimeString();
        addData(priceChart, time, item.price);
      });

      if (tickerData.length > 0)
        lastUpdated = tickerData[tickerData.length - 1].created_at;

      while (priceChart.data.labels.length > MAX_PRICE_DEEP)
        removeData(priceChart);
  };
  
  setInterval(function() {
    let tickerSelector = document.getElementById("ticker")
    priceSocket.send(JSON.stringify([tickerSelector.value, lastUpdated]));
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
  response.forEach(item => {
    let time = new Date(item.created_at);
    labels.push(time.toLocaleTimeString());
    prices.push(item.price);
  });
  lastUpdated = response[response.length - 1].created_at;

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

  if (!isSockerInitialized) {
    initSocket();
    isSockerInitialized = true;
  }
}

$(document).ready(function() {
  $('.select-ticker').select2();
  onTickerSelect();
  $(".select-ticker").on("select2:select", function (e) { onTickerSelect(); });
});
