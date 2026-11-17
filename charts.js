function readJsonData(id) {
    const element = document.getElementById(id);

    if (!element) {
        return null;
    }

    try {
        return JSON.parse(element.textContent);
    } catch (error) {
        console.error("Erreur JSON pour :", id, error);
        return null;
    }
}


document.addEventListener("DOMContentLoaded", function () {
    const categoryChartCanvas = document.getElementById("categoryChart");
    const categoryLabels = readJsonData("analyticsCategoryLabels");
    const categoryValues = readJsonData("analyticsCategoryValues");
    const categoryColors = readJsonData("analyticsCategoryColors");

    if (
        categoryChartCanvas &&
        categoryLabels &&
        categoryValues &&
        categoryColors &&
        typeof Chart !== "undefined"
    ) {
        new Chart(categoryChartCanvas, {
            type: "doughnut",
            data: {
                labels: categoryLabels,
                datasets: [{
                    data: categoryValues,
                    backgroundColor: categoryColors,
                    borderColor: "#FFFFFF",
                    borderWidth: 2,
                    hoverOffset: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "58%",
                plugins: {
                    legend: {
                        position: "bottom"
                    }
                }
            }
        });
    }

    const evolutionChartCanvas = document.getElementById("evolutionChart");
    const evolutionLabels = readJsonData("analyticsEvolutionLabels");
    const evolutionIncome = readJsonData("analyticsEvolutionIncome");
    const evolutionExpenses = readJsonData("analyticsEvolutionExpenses");

    if (
        evolutionChartCanvas &&
        evolutionLabels &&
        evolutionIncome &&
        evolutionExpenses &&
        typeof Chart !== "undefined"
    ) {
        new Chart(evolutionChartCanvas, {
            type: "line",
            data: {
                labels: evolutionLabels,
                datasets: [
                    {
                        label: "Revenus",
                        data: evolutionIncome,
                        borderColor: "#16A34A",
                        backgroundColor: "rgba(22, 163, 74, 0.14)",
                        borderWidth: 3,
                        fill: true,
                        tension: 0.35,
                        pointRadius: 4,
                        pointHoverRadius: 6
                    },
                    {
                        label: "Dépenses",
                        data: evolutionExpenses,
                        borderColor: "#EF4444",
                        backgroundColor: "rgba(239, 68, 68, 0.12)",
                        borderWidth: 3,
                        fill: true,
                        tension: 0.35,
                        pointRadius: 4,
                        pointHoverRadius: 6
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "bottom"
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function (value) {
                                return value.toLocaleString() + " XOF";
                            }
                        }
                    }
                }
            }
        });
    }

    document.querySelectorAll(".category-badge[data-color]").forEach(function (badge) {
        const color = badge.dataset.color;

        if (color) {
            badge.style.backgroundColor = color + "20";
            badge.style.color = color;
        }
    });

    document.querySelectorAll(".progress-bar[data-width]").forEach(function (bar) {
        const width = parseFloat(bar.dataset.width);

        if (!isNaN(width)) {
            bar.style.width = Math.min(Math.max(width, 0), 100) + "%";
        }
    });

    const dashboardChartCanvas = document.getElementById("dashboardChart");
const dashboardLabels = readJsonData("dashboardChartData");
const dashboardValues = readJsonData("dashboardChartValues");
const dashboardColors = readJsonData("dashboardChartColors");

if (
    dashboardChartCanvas &&
    dashboardLabels &&
    dashboardValues &&
    dashboardColors &&
    typeof Chart !== "undefined"
) {
    new Chart(dashboardChartCanvas, {
        type: "doughnut",
        data: {
            labels: dashboardLabels,
            datasets: [{
                data: dashboardValues,
                backgroundColor: dashboardColors,
                borderColor: "#FFFFFF",
                borderWidth: 2,
                hoverOffset: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: "58%",
            plugins: {
                legend: {
                    position: "bottom"
                }
            }
        }
    });
}

const dashboardEvolutionCanvas = document.getElementById("spendingEvolutionChart");
const dashboardEvolutionLabels = readJsonData("spendingEvolutionLabels");
const dashboardEvolutionValues = readJsonData("spendingEvolutionValues");

if (
    dashboardEvolutionCanvas &&
    dashboardEvolutionLabels &&
    dashboardEvolutionValues &&
    typeof Chart !== "undefined"
) {
    new Chart(dashboardEvolutionCanvas, {
        type: "line",
        data: {
            labels: dashboardEvolutionLabels,
            datasets: [{
                label: "Dépenses",
                data: dashboardEvolutionValues,
                borderColor: "#EF4444",
                backgroundColor: "rgba(239, 68, 68, 0.12)",
                borderWidth: 3,
                fill: true,
                tension: 0.35,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "bottom"
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function (value) {
                            return value.toLocaleString() + " XOF";
                        }
                    }
                }
            }
        }
    });
}

document.querySelectorAll(".reference-progress-fill[data-width]").forEach(function (bar) {
    const width = parseFloat(bar.dataset.width);

    if (!isNaN(width)) {
        bar.style.width = Math.min(Math.max(width, 0), 100) + "%";
    }
});
});