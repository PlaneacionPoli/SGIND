// Archivo de JavaScript para el Dashboard Ejecutivo

document.addEventListener("DOMContentLoaded", () => {
    // Configuración de gráficos con Chart.js
    const ctx1 = document.getElementById('chart1').getContext('2d');
    const chart1 = new Chart(ctx1, {
        type: 'bar',
        data: {
            labels: ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo'],
            datasets: [{
                label: 'Indicadores de Progreso',
                data: [12, 19, 3, 5, 2],
                backgroundColor: [
                    'rgba(75, 192, 192, 0.2)',
                    'rgba(54, 162, 235, 0.2)',
                    'rgba(255, 206, 86, 0.2)',
                    'rgba(231, 233, 237, 0.2)',
                    'rgba(153, 102, 255, 0.2)'
                ],
                borderColor: [
                    'rgba(75, 192, 192, 1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(231, 233, 237, 1)',
                    'rgba(153, 102, 255, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'Indicadores de Progreso Mensual'
                }
            }
        }
    });

    const ctx2 = document.getElementById('chart2').getContext('2d');
    const chart2 = new Chart(ctx2, {
        type: 'line',
        data: {
            labels: ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo'],
            datasets: [{
                label: 'Tendencia de Crecimiento',
                data: [3, 10, 5, 2, 20],
                borderColor: 'rgba(255, 99, 132, 1)',
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'Tendencia de Crecimiento'
                }
            }
        }
    });

    // Configuración del gráfico Sunburst
    const ctxSunburst = document.getElementById('sunburstChart').getContext('2d');
    const sunburstData = {
        labels: ['Línea 1', 'Línea 2', 'Objetivo 1', 'Objetivo 2'],
        datasets: [{
            data: [50, 30, 15, 5],
            backgroundColor: ['#4CAF50', '#FFC107', '#2196F3', '#F44336']
        }]
    };

    const sunburstChart = new Chart(ctxSunburst, {
        type: 'doughnut', // Simulación de Sunburst
        data: sunburstData,
        options: {
            plugins: {
                legend: {
                    position: 'top'
                },
                title: {
                    display: true,
                    text: 'Jerarquía Línea → Objetivo'
                }
            }
        }
    });

    // Configuración del gráfico Treemap
    const ctxTreemap = document.getElementById('treemapChart').getContext('2d');
    const treemapData = {
        labels: ['Factor 1', 'Factor 2', 'Característica 1', 'Característica 2'],
        datasets: [{
            data: [40, 30, 20, 10],
            backgroundColor: ['#4CAF50', '#FFC107', '#2196F3', '#F44336']
        }]
    };

    const treemapChart = new Chart(ctxTreemap, {
        type: 'bar', // Simulación de Treemap
        data: treemapData,
        options: {
            plugins: {
                legend: {
                    position: 'top'
                },
                title: {
                    display: true,
                    text: 'Indicadores por Factor y Característica'
                }
            }
        }
    });

    // Configuración del gráfico de Comparativos Históricos
    const ctxHistorical = document.getElementById('historicalComparisonChart').getContext('2d');
    const historicalData = {
        labels: ['2024', '2025', '2026'],
        datasets: [
            {
                label: 'Indicador A',
                data: [75, 80, 85],
                borderColor: 'rgba(75, 192, 192, 1)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                tension: 0.4
            },
            {
                label: 'Indicador B',
                data: [60, 65, 70],
                borderColor: 'rgba(255, 99, 132, 1)',
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                tension: 0.4
            }
        ]
    };

    const historicalComparisonChart = new Chart(ctxHistorical, {
        type: 'line',
        data: historicalData,
        options: {
            plugins: {
                legend: {
                    position: 'top'
                },
                title: {
                    display: true,
                    text: 'Comparativos Históricos entre Periodos'
                }
            },
            responsive: true
        }
    });

    // Configuración del gráfico de Proyecciones de Cumplimiento Futuro
    const ctxFutureProjection = document.getElementById('futureProjectionChart').getContext('2d');
    const futureProjectionData = {
        labels: ['2026', '2027', '2028'],
        datasets: [
            {
                label: 'Proyección Indicador A',
                data: [85, 90, 95],
                borderColor: 'rgba(54, 162, 235, 1)',
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                tension: 0.4
            },
            {
                label: 'Proyección Indicador B',
                data: [70, 75, 80],
                borderColor: 'rgba(255, 206, 86, 1)',
                backgroundColor: 'rgba(255, 206, 86, 0.2)',
                tension: 0.4
            }
        ]
    };

    const futureProjectionChart = new Chart(ctxFutureProjection, {
        type: 'line',
        data: futureProjectionData,
        options: {
            plugins: {
                legend: {
                    position: 'top'
                },
                title: {
                    display: true,
                    text: 'Proyecciones de Cumplimiento Futuro'
                }
            },
            responsive: true
        }
    });

    // Función para filtrar datos según el mes seleccionado
    const filtroMes = document.getElementById('filtro-mes');

    filtroMes.addEventListener('change', (event) => {
        const mesSeleccionado = event.target.value;

        // Lógica para actualizar los gráficos según el mes seleccionado
        if (mesSeleccionado === 'todos') {
            chart1.data.datasets[0].data = [12, 19, 3, 5, 2];
            chart2.data.datasets[0].data = [3, 10, 5, 2, 20];
        } else {
            const meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo'];
            const indice = meses.indexOf(mesSeleccionado);

            chart1.data.datasets[0].data = chart1.data.datasets[0].data.map((_, i) => (i === indice ? [12, 19, 3, 5, 2][i] : 0));
            chart2.data.datasets[0].data = chart2.data.datasets[0].data.map((_, i) => (i === indice ? [3, 10, 5, 2, 20][i] : 0));
        }

        chart1.update();
        chart2.update();
    });
});