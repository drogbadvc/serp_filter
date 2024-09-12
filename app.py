from flask import Flask, request, jsonify, render_template_string
import requests

app = Flask(__name__)

# HTML Template with Bootstrap integration
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SERP Comparison</title>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    <style>
        /* Color for rank differences */
        .diff-green {
            color: green;
        }

        .diff-red {
            color: red;
        }

        .diff-out {
            color: orange;
        }

        .diff-in {
            color: blue;
        }

        h2 {
            text-align: center;
            margin-bottom: 20px;
            color: #343a40;
        }

        /* Truncate long URLs */
        .truncate-url {
            max-width: 250px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .table th, .table td {
            vertical-align: middle;
        }

        .table thead th {
            background-color: #f8f9fa;
        }

        .table td {
            font-size: 14px;
        }

        /* Responsive table container */
        .table-responsive {
            overflow-x: auto;
        }
    </style>
</head>
<body>
    <div class="container-fluid">
        <h1 class="text-center">Compare SERP Rankings</h1>
        <form method="POST" action="/" id="serp-form" class="text-center mb-4">
            <div class="form-group">
                <label for="query">Enter Search Query:</label>
                <input type="text" id="query" name="query" class="form-control d-inline-block" style="width: 300px;" required>
            </div>
            <div class="form-group">
                <label for="hl">Select Language (hl):</label>
                <select id="hl" name="hl" class="form-control d-inline-block" style="width: 150px;" required>
                    <option value="en">English</option>
                    <option value="fr">French</option>
                </select>
                <label for="gl">Select Region (gl):</label>
                <select id="gl" name="gl" class="form-control d-inline-block" style="width: 150px;" required>
                    <option value="US">United States</option>
                    <option value="FR">France</option>
                </select>
                <label for="num">Number of Results:</label>
                <select id="num" name="num" class="form-control d-inline-block" style="width: 100px;" required>
                    <option value="10">10</option>
                    <option value="30">30</option>
                    <option value="50">50</option>
                    <option value="100">100</option>
                </select>
            </div>
            <button type="submit" class="btn btn-primary">Compare</button>
        </form>

        <!-- Bootstrap Grid Structure -->
        <div class="row">
            <div class="col-sm-12 col-md-6 mb-4">
                <h2>Normal</h2>
                <div class="table-responsive">
                    <table id="normal-table" class="table table-bordered table-striped table-hover">
                        <thead>
                            <tr>
                                <th>URL</th>
                                <th>Rank</th>
                                <th>Difference</th>
                            </tr>
                        </thead>
                        <tbody id="normal-tbody">
                            <!-- Normal table data will be inserted here -->
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="col-sm-12 col-md-6 mb-4">
                <h2>Filter=0</h2>
                <div class="table-responsive">
                    <table id="filteroff-table" class="table table-bordered table-striped table-hover">
                        <thead>
                            <tr>
                                <th>URL</th>
                                <th>Rank</th>
                                <th>Difference</th>
                            </tr>
                        </thead>
                        <tbody id="filteroff-tbody">
                            <!-- Filter=0 table data will be inserted here -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <script>
        document.getElementById('serp-form').addEventListener('submit', function(event) {
            event.preventDefault();

            // Clear the previous results
            document.getElementById('normal-tbody').innerHTML = '';
            document.getElementById('filteroff-tbody').innerHTML = '';

            // Get form values
            const query = document.getElementById('query').value;
            const hl = document.getElementById('hl').value;
            const gl = document.getElementById('gl').value;
            const num = document.getElementById('num').value;

            // Send the request to the Flask backend
            fetch('/serp_data', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query, hl, gl, num })
            })
            .then(response => response.json())
            .then(data => {
                // Extract and sort the data by rank
                let normalData = Object.entries(data.serp_data_normal).sort((a, b) => a[1] - b[1]);
                let filterOffData = Object.entries(data.serp_data_filter_off).sort((a, b) => a[1] - b[1]);

                const normalTbody = document.getElementById('normal-tbody');
                const filterOffTbody = document.getElementById('filteroff-tbody');

                // Combine normal and filterOff data into one set of keys
                const allUrls = new Set([...Object.keys(data.serp_data_normal), ...Object.keys(data.serp_data_filter_off)]);

                // Sort the URLs based on their rank, handling missing URLs properly
                const normalRanked = normalData.map(([url, rank]) => ({
                    url, rank, diff: filterOffData.find(([filterUrl]) => filterUrl === url)
                }));

                const filterOffRanked = filterOffData.map(([url, rank]) => ({
                    url, rank, diff: normalData.find(([normalUrl]) => normalUrl === url)
                }));

                // Add sorted data into Normal table
                normalRanked.forEach(({ url, rank, diff }) => {
                    const normalRow = document.createElement('tr');
                    normalRow.innerHTML = `<td class="truncate-url" title="${url}">${url}</td><td>${rank}</td>`;
                    
                    const diffCell = document.createElement('td');
                    if (diff) {
                        const [_, filterRank] = diff;
                        const difference = rank - filterRank;
                        if (difference < 0) {
                            diffCell.innerHTML = `<span class="diff-green">Gained: ${Math.abs(difference)}</span>`;
                        } else if (difference > 0) {
                            diffCell.innerHTML = `<span class="diff-red">Lost: ${Math.abs(difference)}</span>`;
                        } else {
                            diffCell.innerHTML = `<span>No change</span>`;
                        }
                    } else {
                        diffCell.innerHTML = `<span class="diff-out">OUT</span>`;
                    }
                    normalRow.appendChild(diffCell);
                    normalTbody.appendChild(normalRow);
                });

                // Add sorted data into Filter=0 table
                filterOffRanked.forEach(({ url, rank, diff }) => {
                    const filterRow = document.createElement('tr');
                    filterRow.innerHTML = `<td class="truncate-url" title="${url}">${url}</td><td>${rank}</td>`;
                    
                    const diffCell = document.createElement('td');
                    if (diff) {
                        const [_, normalRank] = diff;
                        const difference = normalRank - rank;
                        if (difference < 0) {
                            diffCell.innerHTML = `<span class="diff-green">Gained: ${Math.abs(difference)}</span>`;
                        } else if (difference > 0) {
                            diffCell.innerHTML = `<span class="diff-red">Lost: ${Math.abs(difference)}</span>`;
                        } else {
                            diffCell.innerHTML = `<span>No change</span>`;
                        }
                    } else {
                        diffCell.innerHTML = `<span class="diff-in">IN</span>`;
                    }
                    filterRow.appendChild(diffCell);
                    filterOffTbody.appendChild(filterRow);
                });
            });
        });
    </script>
</body>
</html>

"""


@app.route("/", methods=["GET", "POST"])
def home():
    return render_template_string(HTML_TEMPLATE)


@app.route("/serp_data", methods=["POST"])
def get_serp_data():
    data = request.get_json()

    # Send the request to the FastAPI service for scraping and comparison
    response = requests.post("http://127.0.0.1:8000/scrape", json={
        "search_query": data['query'],
        "hl": data['hl'],
        "gl": data['gl'],
        "num": data['num']
    })

    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({"error": "Failed to retrieve data"}), 500


if __name__ == "__main__":
    app.run(debug=True)
