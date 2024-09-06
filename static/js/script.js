document.addEventListener("DOMContentLoaded", function (e) {
    // Fetch config.json data
    fetch("/config")
        .then((response) => response.json())
        .then((data) => {
            configData = data;
        })
        .catch((error) => {
            console.error("Error loading config.json:", error);
        });

    const webcamVideo = document.getElementById("webcamVideo");

    // Flask
    async function startWebcam() {
        try {
            stream = true;
            document.getElementById("webcamSpinner").style.display = "block";
            webcamVideo.src = "cam_feed?" + new Date().getTime(); // Add a cache-busting query parameter
            webcamVideo.onload = () => {
                document.getElementById("webcamSpinner").style.display = "none";
            };
        } catch (err) {
            console.error("Error accessing webcam:", err);
        }
    }

    function stopWebcam() {
        stream = false;
        document.getElementById("webcamSpinner").style.display = "none";
        webcamVideo.src = "";
    }

    function loadSampleVideo(videoId, videoSrc) {
        const sampleVideo = document.getElementById(videoId);
        sampleVideo.src = videoSrc;
    }

    // Tabs
    document
        .getElementById("webcamToggle")
        .addEventListener("change", function () {
            if (this.checked) {
                startWebcam();
            } else {
                stopWebcam();
            }
        });

    document
        .getElementById("pills-webcam-tab")
        .addEventListener("click", () => {
            document.getElementById("webcamToggle").checked = false;
            document.getElementById("sampleVideo1").pause();
            document.getElementById("sampleVideo2").pause();
            stopWebcam();
        });

    document
        .getElementById("pills-sample1-tab")
        .addEventListener("click", () => {
            document.getElementById("webcamToggle").checked = false;
            document.getElementById("sampleVideo2").pause();
            stopWebcam();
            loadSampleVideo("sampleVideo1", "static/video/out/day1.mp4");
        });

    document
        .getElementById("pills-sample2-tab")
        .addEventListener("click", () => {
            document.getElementById("webcamToggle").checked = false;
            document.getElementById("sampleVideo1").pause();
            stopWebcam();
            loadSampleVideo("sampleVideo2", "static/video/out/day2.mp4");
        });

    document.getElementById("pills-home-tab").addEventListener("click", () => {
        document.getElementById("webcamToggle").checked = false;
        document.getElementById("sampleVideo1").pause();
        document.getElementById("sampleVideo2").pause();
        stopWebcam();
    });

    document
        .getElementById("pills-setting-tab")
        .addEventListener("click", () => {
            document.getElementById("webcamToggle").checked = false;
            document.getElementById("sampleVideo1").pause();
            document.getElementById("sampleVideo2").pause();
            stopWebcam();
        });

    // Shutdown
    setTimeout(() => {
        document
            .getElementById("shutdownDevice")
            .addEventListener("click", () => {
                fetch("shutdown").then((response) => response);
            });

        document
            .getElementById("restartDevice")
            .addEventListener("click", () => {
                fetch("restart").then((response) => response);
            });
    }, 1000);

    // Config
    document
        .getElementById("configurationReview")
        .addEventListener("click", function () {
            const iou =
                parseFloat(document.getElementById("inputIoU").value) ||
                `${configData.cam.iou} (current)`;
            const conf =
                parseFloat(document.getElementById("inputConfidence").value) ||
                `${configData.cam.confidence} (current)`;
            const density =
                parseFloat(document.getElementById("inputDensity").value) ||
                `${configData.cam.density} (current)`;
            const inputAreaValue = document.getElementById("inputPop").value;
            const area = inputAreaValue
                ? `${parseFloat(inputAreaValue)} m²`
                : `${configData.cam.area} m² (current)`;
            let coordinates = getCoordinatesArray();
            coordinates =
                coordinates.length > 0
                    ? coordinates
                    : `${configData.cam.array} (current)`;

            // Update modal content
            document.getElementById("modalIoU").textContent = iou;
            document.getElementById("modalConfidence").textContent = conf;
            document.getElementById("modalPopulation").textContent = area;
            document.getElementById("modalZone").textContent = coordinates;
            document.getElementById("modalDensity").textContent = density;
        });

    // Config Submit
    setTimeout(() => {
        // Function to handle form submission
        document
            .getElementById("confirmConfigSubmit")
            .addEventListener("click", function () {
                // event.preventDefault(); // Prevent form submission
                // Get form input values
                const iou =
                    parseFloat(document.getElementById("inputIoU").value) ||
                    configData.cam.iou;
                const conf =
                    parseFloat(
                        document.getElementById("inputConfidence").value
                    ) || configData.cam.confidence;
                const density =
                    parseFloat(document.getElementById("inputDensity").value) ||
                    configData.cam.density;
                const area =
                    parseFloat(document.getElementById("inputPop").value) ||
                    configData.cam.area;
                let coordinates = getCoordinatesArray();
                coordinates =
                    coordinates.length > 0 ? coordinates : configData.cam.array;

                // Create an object with the values
                let settings = {
                    iou: iou,
                    confidence: conf,
                    area: area,
                    array: coordinates,
                    density: density,
                };

                // Send the settings object to your server to edit the JSON file
                fetch("/set", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify(settings),
                })
                    .then((response) => response.json())
                    .then((data) => {
                        console.log("Settings updated:", data);
                        fetch("daemonrestart").then((response) => response);
                    })
                    .catch((error) => {
                        console.error("Error updating settings:", error);
                    });

                setTimeout(() => {
                    location.reload();
                }, 3000);
            });
    }, 1000);

    // Polygon Coordinates
    let coordinateCount = 0;
    const minCoordinates = 3;
    const coordinatesList = document.getElementById("coordinatesList");
    const addCoordinateButton = document.getElementById("addCoordinate");

    function addCoordinate() {
        const coordinateDiv = document.createElement("div");
        coordinateDiv.className = "input-group mb-2";
        coordinateDiv.innerHTML = `
            <input type="number" name="xCoordinate${coordinateCount}" class="form-control" step="1" min="0" placeholder="X" required />
            <input type="number" name="yCoordinate${coordinateCount}" class="form-control" step="1" min="0" placeholder="Y" required />
            <button type="button" class="btn btn-danger btn-sm removeCoordinate"><i class="bi bi-x-lg"></i></button>
        `;
        coordinatesList.appendChild(coordinateDiv);

        coordinateDiv
            .querySelector(".removeCoordinate")
            .addEventListener("click", function () {
                coordinatesList.removeChild(coordinateDiv);
                coordinateCount--;
                checkCoordinateCount();
            });

        coordinateCount++;
        checkCoordinateCount();
    }

    function checkCoordinateCount() {
        const removeButtons = document.querySelectorAll(".removeCoordinate");
        removeButtons.forEach((button) => {
            button.disabled = coordinateCount <= minCoordinates;
        });
    }

    addCoordinateButton.addEventListener("click", addCoordinate);

    for (let i = 0; i < minCoordinates; i++) {
        addCoordinate();
    }

    function getCoordinatesArray() {
        const coordinates = [];
        const xInputs = document.querySelectorAll('input[name^="xCoordinate"]');
        const yInputs = document.querySelectorAll('input[name^="yCoordinate"]');

        for (let i = 0; i < xInputs.length; i++) {
            const xValue = parseFloat(xInputs[i].value);
            const yValue = parseFloat(yInputs[i].value);
            if (!isNaN(xValue) && !isNaN(yValue)) {
                coordinates.push(xValue, yValue);
            }
        }

        return coordinates;
    }

    // Tooltip
    const tooltipTriggerList = document.querySelectorAll(
        '[data-bs-toggle="tooltip"]'
    );
    const tooltipList = [...tooltipTriggerList].map(
        (tooltipTriggerEl) => new bootstrap.Tooltip(tooltipTriggerEl)
    );
});
