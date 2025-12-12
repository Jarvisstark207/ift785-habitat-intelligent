let tempChart = null;
let consumptionChart = null;

function initCharts() {
    const tempCtx = document.getElementById('tempChart').getContext('2d');
    tempChart = new Chart(tempCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Salon',
                    data: [],
                    borderColor: 'rgb(255, 99, 132)',
                    backgroundColor: 'rgba(255, 99, 132, 0.1)',
                    tension: 0.3
                },
                {
                    label: 'Cuisine',
                    data: [],
                    borderColor: 'rgb(54, 162, 235)',
                    backgroundColor: 'rgba(54, 162, 235, 0.1)',
                    tension: 0.3
                },
                {
                    label: 'Chambre',
                    data: [],
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.1)',
                    tension: 0.3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'top',
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    title: {
                        display: true,
                        text: 'Temperature (°C)'
                    }
                }
            }
        }
    });

    const consumptionCtx = document.getElementById('consumptionChart').getContext('2d');
    consumptionChart = new Chart(consumptionCtx, {
        type: 'bar',
        data: {
            labels: ['Salon', 'Cuisine', 'Chambre'],
            datasets: [{
                label: 'Consommation (W)',
                data: [0, 0, 0],
                backgroundColor: [
                    'rgba(255, 99, 132, 0.5)',
                    'rgba(54, 162, 235, 0.5)',
                    'rgba(75, 192, 192, 0.5)'
                ],
                borderColor: [
                    'rgb(255, 99, 132)',
                    'rgb(54, 162, 235)',
                    'rgb(75, 192, 192)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Watts'
                    }
                }
            }
        }
    });
}

function updateGlobalStats(data) {
    document.getElementById('global-consumption').textContent = 
        data.total_consumption !== null ? data.total_consumption.toFixed(1) : '--';
    document.getElementById('global-occupied').textContent = data.occupied_rooms;
    document.getElementById('global-temp').textContent = 
        data.avg_temp !== null ? data.avg_temp.toFixed(1) : '--';
}

function updateLocationCard(location, stats) {
    const prefix = location;
    
    document.getElementById(`${prefix}-temp`).textContent = 
        stats.temp_avg !== null ? `${stats.temp_avg}°C` : '--';
    
    const minMax = (stats.temp_min !== null && stats.temp_max !== null) 
        ? `${stats.temp_min}°C / ${stats.temp_max}°C` 
        : '--';
    document.getElementById(`${prefix}-temp-range`).textContent = minMax;
    
    document.getElementById(`${prefix}-lux`).textContent = 
        stats.luminosity !== null ? `${stats.luminosity} lux` : '--';
    
    document.getElementById(`${prefix}-movement`).textContent = 
        stats.movement ? 'Oui' : 'Non';
    
    document.getElementById(`${prefix}-consumption`).textContent = 
        stats.consumption !== null ? `${stats.consumption} W` : '--';
}

function updateAlerts(alerts) {
    const alertsSection = document.getElementById('alerts-section');
    const alertsList = document.getElementById('alerts-list');
    
    if (alerts.length > 0) {
        alertsSection.style.display = 'block';
        alertsList.innerHTML = alerts.map(alert => 
            `<div class="alert-item">${alert}</div>`
        ).join('');
    } else {
        alertsSection.style.display = 'none';
    }
}

function updateTemperatureChart(tempHistory) {
    if (!tempHistory || Object.keys(tempHistory).length === 0) return;
    
    const salonData = tempHistory.salon || [];
    const cuisineData = tempHistory.cuisine || [];
    const chambreData = tempHistory.chambre || [];
    
    const maxLength = Math.max(salonData.length, cuisineData.length, chambreData.length);
    
    if (maxLength === 0) return;
    
    const labels = [];
    for (let i = 0; i < maxLength; i++) {
        labels.push(`-${maxLength - i}`);
    }
    
    tempChart.data.labels = labels;
    tempChart.data.datasets[0].data = salonData.map(d => d.value);
    tempChart.data.datasets[1].data = cuisineData.map(d => d.value);
    tempChart.data.datasets[2].data = chambreData.map(d => d.value);
    tempChart.update();
}

function updateConsumptionChart(consumptionData) {
    if (!consumptionData) return;
    
    consumptionChart.data.datasets[0].data = [
        consumptionData.salon || 0,
        consumptionData.cuisine || 0,
        consumptionData.chambre || 0
    ];
    consumptionChart.update();
}

function updateHistoryTable(recent) {
    const tbody = document.getElementById('history-tbody');
    
    if (recent.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5">Aucune donnee</td></tr>';
        return;
    }
    
    tbody.innerHTML = recent.map(row => {
        const timestamp = new Date(row.timestamp);
        const timeStr = timestamp.toLocaleTimeString('fr-CA');
        const dateStr = timestamp.toLocaleDateString('fr-CA');
        
        return `
            <tr>
                <td>${dateStr} ${timeStr}</td>
                <td>${row.location}</td>
                <td>${row.type}</td>
                <td>${row.value}</td>
                <td>${row.unit}</td>
            </tr>
        `;
    }).join('');
}

async function fetchData() {
    try {
        const response = await fetch('/api/data');
        const data = await response.json();
        
        updateGlobalStats(data.global);
        
        updateLocationCard('salon', data.locations.salon);
        updateLocationCard('cuisine', data.locations.cuisine);
        updateLocationCard('chambre', data.locations.chambre);
        
        updateAlerts(data.alerts);
        
        updateTemperatureChart(data.temperature_history);
        updateConsumptionChart(data.consumption_current);
        
        updateHistoryTable(data.recent);
        
    } catch (error) {
        console.error('Erreur fetch:', error);
    }
}

window.addEventListener('DOMContentLoaded', () => {
    initCharts();
    fetchData();
    setInterval(fetchData, 5000);
});
