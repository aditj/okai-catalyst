
### **Project: Catalyst MVP - Developer Todo List**

**Goal:** Build a working prototype that allows a user to receive a unique manufacturing case study, submit their analysis, and get an AI-powered evaluation and score.


### **Phase 1: Build the Static Frontend**
**(Based on MVP Todo #1)**


[x] **1. Create a `CaseStudy` Component:**
    * In the `frontend/src` folder, create a new folder called `components`.
    * Inside `components`, create a file `CaseStudy.js`.
    * In this file, create a simple component that displays a hardcoded case study title and text.
        * **Example Text:** "Case Study: Unexplained Defects on Assembly Line 3. For the past week, the final quality check on Assembly Line 3 has seen a 15% increase in product defects. The defects are minor scratches on the product housing. This is causing rework delays and increasing material waste. Your task is to analyze this problem."

[x] **2. Create a `ResponseForm` Component:**
    * In the `components` folder, create a file `ResponseForm.js`.
    * This component should contain:
        * A `<textarea>` element for the user to type their analysis. Use the `useState` hook to store the text as the user types.
        * A `<button>` with the text "Submit Analysis".

[x] **3. Assemble the Main App Page:**
    * Open `frontend/src/App.js`.
    * Import your `CaseStudy` and `ResponseForm` components.
    * Arrange them on the page so the case study appears at the top and the response form is below it.
    * **Checkpoint:** Run `npm start`. You should see a static webpage showing the case study text, a text box, and a submit button. The button won't do anything yet.

---

### **Phase 2: Build the Backend Evaluation Service**
**(Based on MVP Todo #2)**


[x] **2. Create the Basic Express Server:**
    * In the `backend` folder, create a file named `server.js`.
    * Set up a basic Express server that listens on a port (e.g., 8000). Remember to include `cors()` to allow requests from your frontend.

[x] **3. Create the `/evaluate` Endpoint:**
    * In `server.js`, create a `POST` endpoint at the path `/api/evaluate`.
    * This endpoint will receive the user's analysis text in the request body (e.g., `req.body.analysisText`).

[x] **4. Implement the LLM Evaluation Logic:**
    * Inside the `/evaluate` endpoint, initialize the Google AI client using your API key from the `.env` file.
    * Create a detailed **prompt** that instructs the LLM how to behave.
        * **Prompt Template:**
            ```javascript
            const userAnalysis = req.body.analysisText;
            const prompt = `
              You are an expert Operational Excellence consultant. Evaluate the following problem analysis from a manufacturing manager.
              Based on the analysis below, provide a score out of 10 for "Root Cause Identification" and a score out of 10 for "Solution Practicality".
              Also, provide a short paragraph of constructive feedback (2-3 sentences).
              Format your response as a JSON object with three keys: "rootCauseScore", "solutionScore", and "feedback".

              Here is the manager's analysis:
              "${userAnalysis}"
            `;
            ```
    * Send this prompt to the LLM API.
    * Parse the LLM's JSON response and send it back to the client using `res.json(...)`.

[x] **5. Test the Endpoint:**
    * Use a tool like **Postman** or **Insomnia** to send a `POST` request to `http://localhost:8000/api/evaluate`.
    * Include a sample JSON body like `{ "analysisText": "The problem is scratches. I think the machine is old. We should buy a new one." }`.
    * **Checkpoint:** Verify that you receive a valid JSON response from your server with scores and feedback.

---

### **Phase 3: Connect Frontend & Backend**
**(Based on MVP Todo #3)**

[x] **1. Implement the `fetch` Call:**
    * Go back to your `ResponseForm.js` component in the frontend.
    * Create a function to handle the form submission. This function will be called when the button is clicked.
    * Inside this function, use the `fetch` API to make a `POST` request to your backend's `/api/evaluate` endpoint, sending the user's text in the body.

[x] **2. Manage Application State:**
    * In your `App.js` file, use `useState` to create state variables for:
        * `results` (to store the scores and feedback from the backend).
        * `isLoading` (to show a loading message while waiting for the API response).

[x] **3. Display the Results:**
    * Create a new `Results.js` component that takes the `results` object as a prop and displays the scores and feedback nicely.
    * In `App.js`, use **conditional rendering**:
        * If `isLoading` is true, show a "Loading..." message.
        * If `results` is not null, hide the `ResponseForm` and show the `Results` component.
        * Otherwise, show the `ResponseForm`.
    * **Checkpoint:** Run both the frontend (`npm start`) and backend (`node server.js`). You should now be able to type an analysis, click submit, see a loading state, and then see the AI-generated results appear on the screen.

---

### **Phase 4: Implement Dynamic Case Generation**
**(Based on MVP Todo #4)**

[x] **1. Create a New Backend Endpoint:**
    * In your `backend/server.js` file, create a new `GET` endpoint at `/api/generate-case`.

[x] **2. Implement LLM Case Generation Logic:**
    * Inside this new endpoint, call the Google AI API with a prompt to generate a case study.
        * **Prompt Template:** ` "You are a manufacturing process expert. Write a short, single-paragraph case study (about 100 words) about a common operational problem in a factory. The problem could be about quality, safety, or production delays. Do not include the solution."`
    * Send the text response from the LLM back to the client.

[x] **3. Fetch the Case Study on the Frontend:**
    * In your `frontend/src/App.js` file, replace the hardcoded case study text.
    * Use the `useEffect` hook to call your new `/api/generate-case` endpoint when the application first loads.
    * Store the returned case study text in a state variable (e.g., `useState('')`).
    * Pass this state variable as a prop to your `CaseStudy` component.
    * **Checkpoint:** Refresh your application multiple times. Each time, you should see a new, unique case study generated by the AI, completing the full MVP functionality.