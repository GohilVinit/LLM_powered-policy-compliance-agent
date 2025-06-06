

const API_BASE_URL = "http://localhost:8000";

// Populate available JSON files into dropdowns
async function populateJsonFiles() {
    console.log("Fetching JSON files...");
    try {
        const response = await fetch(`${API_BASE_URL}/list-json-files/`);
        const result = await response.json();

        console.log(result);

        const jsonFileSelect = document.getElementById("json-file");
        const jsonFilesSelect = document.getElementById("json-files");

        if (!jsonFileSelect || !jsonFilesSelect) {
            console.error("Dropdown elements not found.");
            return;
        }

        // Clear previous options
        jsonFileSelect.innerHTML = '<option value="">--Select JSON File--</option>';
        jsonFilesSelect.innerHTML = '<option value="">--Select JSON File--</option>';

        if (response.ok && result.json_files?.length > 0) {
            result.json_files.forEach(file => {
                const option1 = new Option(file, file);
                const option2 = new Option(file, file);
                jsonFileSelect.add(option1);
                jsonFilesSelect.add(option2);
            });
        } else {
            const emptyOption = new Option("No JSON files available", "");
            jsonFileSelect.add(emptyOption);
            jsonFilesSelect.add(emptyOption.cloneNode(true));
        }
    } catch (error) {
        console.error("Error fetching JSON files:", error);
        alert("An error occurred while fetching JSON files. Please try again.");
    }
}


async function uploadPolicy(inputId, isBank = false) {
    const input = document.getElementById(inputId);
    const uploadDetailsDiv = document.getElementById("upload-details");

    if (!input.files.length) {
        setStatus("Please select a file to upload", "error");
        uploadDetailsDiv.innerHTML = "";
        return;
    }

    const formData = new FormData();
    formData.append("file", input.files[0]);
    formData.append("is_bank", isBank);

    try {
        setStatus("Uploading...");

        // Add a timeout to the fetch request (e.g., 30 seconds)
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 seconds timeout

        const response = await fetch(`${API_BASE_URL}/upload-policy/`, {
            method: "POST",
            body: formData,
            signal: controller.signal
        });

        clearTimeout(timeoutId); // Clear the timeout if the request completes

        const result = await response.json();

        if (response.ok) {
            setStatus(result.message || "File uploaded successfully!", "success");
            // Display detailed upload information
            uploadDetailsDiv.innerHTML = `
                <h3>Upload Details</h3>
                <p><strong>Message:</strong> ${result.message || "N/A"}</p>
                <p><strong>Generated JSON File:</strong> ${result.json_file || "N/A"}</p>
                <p><strong>Milvus Collection:</strong> ${result.milvus_collection || "N/A"}</p>
            `;
            populateJsonFiles(); // Refresh file list
        } else {
            setStatus(result.detail || "Upload failed", "error");
            uploadDetailsDiv.innerHTML = `<p style="color: red;">Error: ${result.detail || "Upload failed"}</p>`;
        }
    } catch (error) {
        console.error("Upload error:", error);
        let errorMessage = "Upload error: " + error.message;
        if (error.name === "AbortError") {
            errorMessage = "Upload timed out after 30 seconds. Please try again.";
        }
        setStatus(errorMessage, "error");
        uploadDetailsDiv.innerHTML = `<p style="color: red;">${errorMessage}</p>`;
    }
}
// Generate questions from selected policy
async function generateQuestions() {
    const selectedFile = document.getElementById("json-file").value;

    if (!selectedFile) {
        setStatus("Please select a JSON file", "error");
        return;
    }

    try {
        setStatus("Generating questions...");

        const response = await fetch(`${API_BASE_URL}/generate-questions/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ json_file: selectedFile })
        });

        const result = await response.json();

        if (response.ok) {
            setStatus(result.message || "Questions generated successfully!", "success");
            populateJsonFiles(); // Refresh after generating new file
        } else {
            setStatus(result.detail || "Failed to generate questions", "error");
        }
    } catch (error) {
        console.error("Generate questions error:", error);
        setStatus(`Network error: ${error.message}`, "error");
    }
}

// Show selected file content
async function showfile() {
    const fileInput = document.getElementById("json-files");
    const selectedFile = fileInput.value;
    const fileContent = document.getElementById("results");

    fileContent.innerHTML = "";

    if (!selectedFile) {
        setStatus("Please select a file to view", "error");
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/get-file-content/?filename=${encodeURIComponent(selectedFile)}`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Failed to load file");
        }

        console.log("Selected file:", selectedFile);
        console.log("Fetched data:", data);
        console.log("Data type:", Array.isArray(data) ? "Array" : typeof data);

        let formattedContent = "";
        // Check if file is a questions JSON based on suffix
        if (selectedFile.endsWith("_questions.json")) {
            // Questions JSON (e.g., Bank_Policy_questions.json)
            if (data && typeof data === "object" && !Array.isArray(data)) {
                Object.entries(data).forEach(([topic, questions]) => {
                    if (Array.isArray(questions)) {
                        formattedContent += `
                            <div style="border: 1px solid #ccc; padding: 10px; margin-bottom: 10px; border-radius: 8px;">
                                <h3>${topic}</h3>
                                <p><strong>Questions:</strong></p>
                                <ul>
                                    ${questions.map(q => `<li>${q}</li>`).join("")}
                                </ul>
                            </div>
                        `;
                    } else {
                        formattedContent += `
                            <div style="border: 1px solid #ccc; padding: 10px; margin-bottom: 10px; border-radius: 8px;">
                                <h3>${topic}</h3>
                                <p><strong>Error:</strong> Invalid questions format</p>
                            </div>
                        `;
                    }
                });
            } else {
                throw new Error("Invalid questions JSON format");
            }
        } else {
            // Policy JSON (e.g., Bank_Policy.json)
            if (Array.isArray(data)) {
                data.forEach(item => {
                    formattedContent += `
                        <div style="border: 1px solid #ccc; padding: 10px; margin-bottom: 10px; border-radius: 8px;">
                            <h3>${item.topic_name}</h3>
                            <p><strong>Paragraph:</strong> ${item.full_paragraph}</p>
                            <p><strong>Keywords:</strong> ${item.keywords.join(", ")}</p>
                        </div>
                    `;
                });
            } else {
                throw new Error("Invalid policy JSON format");
            }
        }

        fileContent.innerHTML = formattedContent;
        setStatus(`Displaying content of '${selectedFile}'`, "success");
    } catch (error) {
        console.error("Error displaying file:", error);
        fileContent.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
        setStatus(`Error displaying file: ${error.message}`, "error");
    }
}

// Show compliance results
async function showResults() {
    const fileContent = document.getElementById("results");

    // Clear previous content
    fileContent.innerHTML = "<p>Loading compliance results...</p>";
    setStatus("Fetching compliance results...");

    try {
        // Try to fetch from the API endpoint first
        let response = await fetch(`${API_BASE_URL}/compliance-results/`);
        
        // If API fails, try to load the file directly
        if (!response.ok) {
            console.log("API endpoint not available, trying direct file access...");
            response = await fetch(`${API_BASE_URL}/get-file-content/?filename=compliance_results_milvus.json`);
            
            // If that also fails, try the UI data directory
            if (!response.ok) {
                console.log("Direct file access failed, trying UI data directory...");
                response = await fetch(`${API_BASE_URL}/get-file-content/?filename=data/compliance_results_milvus.json`);
            }
            
            // If that still fails, check both variations of the path
            if (!response.ok) {
                console.log("UI data directory failed, trying alternative paths...");
                const alternatives = [
                    "../ui/data/compliance_results_milvus.json",
                ];
                
                for (const path of alternatives) {
                    try {
                        response = await fetch(`${API_BASE_URL}/get-file-content/?filename=${encodeURIComponent(path)}`);
                        if (response.ok) {
                            console.log(`Found file at path: ${path}`);
                            break;
                        }
                    } catch (e) {
                        console.log(`Failed to fetch from ${path}: ${e.message}`);
                    }
                }
            }
        }
        
        // If all attempts failed
        if (!response.ok) {
            throw new Error("Could not find compliance results file. Please run check_compliance.py first.");
        }
        
        const data = await response.json();
        console.log("Compliance results:", data);

        // Validate data structure
        if (!data || typeof data !== "object" || Array.isArray(data) || Object.keys(data).length === 0) {
            throw new Error("Invalid compliance results format or empty results");
        }

        // Track statistics
        let totalQuestions = 0;
        let compliantCount = 0;
        let nonCompliantCount = 0;
        let partiallyCompliantCount = 0;
        let errorCount = 0;

        let formattedContent = "";
        
        // Process each topic
        Object.entries(data).forEach(([topic, results]) => {
            if (!Array.isArray(results) || results.length === 0) {
                formattedContent += `
                    <div style="border: 1px solid #ccc; padding: 10px; margin-bottom: 10px; border-radius: 8px; background-color: #f8d7da;">
                        <h3>${topic}</h3>
                        <p style="color: #721c24;">No valid results found for this topic</p>
                    </div>
                `;
                return;
            }

            formattedContent += `
                <div style="border: 1px solid #ccc; padding: 10px; margin-bottom: 10px; border-radius: 8px;">
                    <h3>${topic}</h3>
                    <ul style="list-style-type: none; padding: 0;">
            `;
            
            // Process each result
            results.forEach(result => {
                totalQuestions++;
                
                // Handle error case
                if (result.error) {
                    errorCount++;
                    formattedContent += `
                        <li style="border: 1px solid #ccc; padding: 10px; margin-bottom: 10px; border-radius: 5px; background-color: #f8d7da;">
                            <strong>Question:</strong> ${result.question || "Unknown question"}<br>
                            <strong>Error:</strong> ${result.error}
                        </li>
                    `;
                    return;
                }
                
                // Determine status styling and count
                let statusStyle = "";
                let statusText = result.compliance_status || "Status not available";
                
                if (result.compliance_status) {
                    const status = result.compliance_status.toLowerCase();
                    if (status.includes("compliant") && !status.includes("non") && !status.includes("partially")) {
                        statusStyle = "background-color: #d4edda; color: #155724;";
                        compliantCount++;
                    } else if (status.includes("non")) {
                        statusStyle = "background-color: #f8d7da; color: #721c24;";
                        nonCompliantCount++;
                    } else if (status.includes("partially")) {
                        statusStyle = "background-color: #fff3cd; color: #856404;";
                        partiallyCompliantCount++;
                    } else {
                        statusStyle = "background-color: #e2e3e5; color: #383d41;";
                    }
                } else {
                    statusStyle = "background-color: #e2e3e5; color: #383d41;";
                    errorCount++;
                }

                // Format the individual result
                formattedContent += `
                    <li style="border: 1px solid #ccc; padding: 10px; margin-bottom: 10px; border-radius: 5px;">
                        <strong>Question:</strong> ${result.question || "No question provided"}<br>
                        <div style="display: inline-block; padding: 3px 8px; border-radius: 4px; margin: 5px 0; ${statusStyle}">
                            <strong>Status:</strong> ${statusText}
                        </div><br>
                        <strong>Bank Answer:</strong> ${result.answer_from_bank || "No answer available"}<br>
                        <strong>Vendor Answer:</strong> ${result.answer_from_vendor || "No answer available"}<br>
                        <strong>Bank Reference:</strong> ${result.reference_bank || "No reference available"}<br>
                        <strong>Vendor Reference:</strong> ${result.reference_vendor || "No reference available"}
                    </li>
                `;
            });
            
            formattedContent += `
                    </ul>
                </div>
            `;
        });

        // Add summary section
        formattedContent += `
            <div style="border: 1px solid #ccc; padding: 10px; margin-bottom: 10px; border-radius: 8px; background-color: #f0f0f0;">
                <h3>Summary</h3>
                <p>
                    Total Questions: ${totalQuestions}<br>
                    <span style="color: #155724;">Compliant: ${compliantCount}</span><br>
                    <span style="color: #721c24;">Non-Compliant: ${nonCompliantCount}</span><br>
                    <span style="color: #856404;">Partially Compliant: ${partiallyCompliantCount}</span><br>
                    <span style="color: #721c24;">Errors: ${errorCount}</span>
                </p>
            </div>
        `;

        fileContent.innerHTML = formattedContent;
        setStatus("Displaying compliance results", "success");
    } catch (error) {
        console.error("Error displaying compliance results:", error);
        fileContent.innerHTML = `
            <div style="border: 1px solid #f8d7da; background-color: #f8d7da; color: #721c24; padding: 15px; border-radius: 8px;">
                <h3>Error Loading Compliance Results</h3>
                <p>${error.message}</p>
                <p>Possible solutions:</p>
                <ol>
                    <li>Make sure you've run <code>check_compliance.py</code> to generate the results file.</li>
                    <li>Check that the file <code>compliance_results_milvus.json</code> exists in the correct location.</li>
                    <li>Verify that the API server is running and properly configured.</li>
                </ol>
            </div>
        `;
        setStatus(`Error displaying compliance results: ${error.message}`, "error");
    }
}


// Set status messages on screen
function setStatus(message, type = "info") {
    const statusDiv = document.getElementById("upload-status");
    const color = type === "error" ? "red" : type === "success" ? "green" : "blue";
    statusDiv.innerHTML = `<p style="color: ${color};">${message}</p>`;
}

// Auto-load when page is ready
window.onload = function() {
    populateJsonFiles();
};