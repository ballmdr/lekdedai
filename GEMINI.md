claude -p "You are a highly skilled Python, Django, and Next.js developer. I am the Project Manager for 'lekdedai', and I understand the deep cultural significance of 'lucky numbers' (เลขเด็ด) for our users. Our goal is to provide a unique, personalized lucky number experience directly on the homepage, accessible to everyone without requiring any user registration or login.

**New Feature: 'Instant Lucky Numbers' (เลขเด็ดทันใจ)**

**Objective:** Create a prominent section on the homepage that generates personalized lucky numbers based on non-identifying user input and real-time data, without requiring any user registration or login.

**Requirements:**

1.  **Homepage Integration (Frontend - `theme` directory):**
    *   Design and implement a new, visually appealing section on the `lekdedai` homepage for "Instant Lucky Numbers."
    *   This section should be immediately visible and interactive upon page load.

2.  **User Input (Non-identifying):**
    *   Include a simple input field where users can optionally enter a "significant date" (e.g., their birthdate, an anniversary, or any date they feel is lucky). This input should *not* be stored or linked to any user profile.
    *   If no date is provided, the system should default to the current date.

3.  **Backend Logic for Number Generation (Django - `app` directory):**
    *   Develop a new, lightweight API endpoint that accepts the "significant date" (or uses the current date) and generates a set of lucky numbers.
    *   **Number Generation Logic:**
        *   **Core Component 1: Date-based:** Extract numbers from the provided date (e.g., day, month, year digits, sums of digits).
        *   **Core Component 2: News-based:** Integrate with our existing news analysis capabilities (`app/news`, `thairath_scraper`) to extract numerical patterns or significant numbers from the most recent 24-48 hours of news. For example, counts of specific keywords, dates mentioned, or statistics.
        *   **Combination:** Combine the numbers from the date and news components using a simple, yet intriguing, algorithm (e.g., concatenation, simple arithmetic operations, or selection based on frequency).
        *   The output should be a small set of 2-digit or 3-digit numbers, suitable for lottery prediction.

4.  **Frontend Display & Interaction:**
    *   Display the generated lucky numbers clearly and attractively.
    *   Add a "Generate New Numbers" button that allows users to re-generate numbers based on the same or a new date.
    *   Ensure fast response times for number generation.

5.  **Considerations:**
    *   **Privacy:** Emphasize that no personal data is stored or tracked.
    *   **Performance:** The generation process must be very fast, as it's for every visitor.
    *   **Scalability:** The solution should be able to handle high traffic without performance degradation.

6.  **Testing:**
    *   Write unit and integration tests for the new API endpoint and the frontend component.

7.  **Documentation:**
    *   Document the new API endpoint, the number generation logic, and frontend integration details.

Please provide a brief technical proposal outlining your approach for both frontend and backend changes, especially focusing on the number generation algorithm and how it leverages news data. Your code should adhere to existing project conventions and best practices."
