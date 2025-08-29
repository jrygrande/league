# Technical Framework for Sleeper League Explorer

This document outlines the proposed technical framework for building a web application to explore Sleeper fantasy football leagues.

## Overview

The goal is to create a data-rich web application with a modern, responsive user interface. The application will fetch data from the Sleeper API and present it to the user in a clean and intuitive way. To achieve this while keeping hosting costs low, we will use a decoupled architecture with a Python backend and a React-based frontend.

## Backend

*   **Framework:** [FastAPI](https://fastapi.tiangolo.com/)
*   **Language:** Python
*   **Key Libraries:**
    *   `httpx` or `requests`: For making asynchronous requests to the Sleeper API.
    *   `pydantic`: For data validation and settings management (comes with FastAPI).

### Why FastAPI?

*   **High Performance:** FastAPI is one of the fastest Python frameworks available.
*   **Easy to Learn:** The syntax is modern, clean, and easy to pick up, especially for those familiar with Python type hints.
*   **Automatic Docs:** It automatically generates interactive API documentation (using Swagger UI and ReDoc), which is great for development and testing.
*   **Asynchronous Support:** FastAPI is built on Starlette and supports asynchronous request handling, which is ideal for an I/O-bound application that will be making many requests to an external API.
*   **Scalability:** It's highly scalable and can be easily deployed in a variety of environments, including serverless platforms.

## Frontend

*   **Framework:** [Next.js](https://nextjs.org/)
*   **Language:** TypeScript
*   **UI Components:** [shadcn/ui](https://ui.shadcn.com/)
*   **Styling:** [Tailwind CSS](https://tailwindcss.com/)

### Why Next.js and shadcn/ui?

*   **Rich User Experience:** Next.js is a powerful React framework that enables the creation of fast and dynamic user interfaces. Features like server-side rendering (SSR) and static site generation (SSG) can be used to optimize performance.
*   **Modern UI:** `shadcn/ui` provides a set of beautifully designed, accessible, and customizable UI components that will allow us to build a professional-looking application quickly.
*   **Developer Experience:** The combination of Next.js, TypeScript, and Tailwind CSS provides a great developer experience.
*   **Strong Community:** Both Next.js and `shadcn/ui` have large and active communities.

## Architecture

We will use a **decoupled (or headless) architecture**.

*   The **backend** will be a RESTful API built with FastAPI. Its sole responsibility will be to handle business logic, fetch data from the Sleeper API, and expose it to the frontend.
*   The **frontend** will be a standalone Next.js application that consumes the data from our FastAPI backend.

This separation of concerns makes the application easier to develop, test, and scale. It also allows us to choose the best technologies for each part of the application.

## Hosting

For the cheapest possible hosting with a great developer experience, we recommend the following:

*   **Frontend (Next.js):** [Vercel](https://vercel.com/)
    *   Vercel offers a generous free tier for personal projects and is built by the creators of Next.js, so the integration is seamless. It provides automatic deployments, CI/CD, and a global CDN.
*   **Backend (FastAPI):** [Vercel Serverless Functions](https://vercel.com/docs/functions/serverless-functions) or [AWS Lambda](https://aws.amazon.com/lambda/)
    *   We can deploy our FastAPI application as a serverless function. This is extremely cost-effective as you only pay for the compute time you use, and the free tiers are often more than enough for a personal project. Vercel's serverless functions are a good option if you want to host both the frontend and backend on the same platform.

## High-Level Development Roadmap

1.  **Setup Backend:** Initialize a FastAPI project and create a basic endpoint to test the setup.
2.  **Setup Frontend:** Initialize a Next.js project with TypeScript and Tailwind CSS.
3.  **Integrate shadcn/ui:** Add `shadcn/ui` to the Next.js project.
4.  **Backend-Sleeper Integration:** Implement the logic in the FastAPI backend to communicate with the Sleeper API. Create endpoints for fetching league data.
5.  **Frontend-Backend Integration:** Connect the Next.js frontend to the FastAPI backend to fetch and display league data.
6.  **Build UI Components:** Create the React components needed to display the data using `shadcn/ui` components.
7.  **Deployment:** Deploy the frontend to Vercel and the backend to a serverless platform.
