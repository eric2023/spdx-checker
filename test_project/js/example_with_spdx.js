/* SPDX-License-Identifier: Apache-2.0
 *
 * Copyright (c) 2025 Example JavaScript Project
 */

function greetUser(name) {
    console.log(`Hello, ${name}! Welcome to SPDX Scanner.`);
}

class MathUtils {
    static add(a, b) {
        return a + b;
    }

    static multiply(a, b) {
        return a * b;
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { greetUser, MathUtils };
}