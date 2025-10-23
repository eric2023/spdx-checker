// SPDX-License-Identifier: MIT
// Copyright (c) 2023 Example Corporation
// Example Project

/**
 * Example JavaScript file demonstrating proper SPDX license header.
 * This file shows how SPDX license declarations should be formatted
 * in JavaScript source code files.
 */

function main() {
    /**
     * Main function demonstrating the SPDX scanner example.
     */
    console.log("This is an example JavaScript file with proper SPDX license header.");
    console.log("The SPDX scanner will recognize this as a valid license declaration.");

    // Example functionality
    const message = "Hello, SPDX!";
    console.log(`Message: ${message}`);

    return 0;
}

if (require.main === module) {
    process.exit(main());
}

module.exports = { main };