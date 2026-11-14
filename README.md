# Trend Detective

Trend Detective is an interactive web platform built for the NASA Space Apps Challenge. Everyday weather fluctuates and seasons repeat every year, making it difficult to tell if a region is actually experiencing long-term environmental change. This tool lets anyone explore satellite observations from NASA and NOAA to see whether observed shifts represent real, multi-decade trends or just ordinary seasonal cycles.

You can pick any location on the map or compare two regions side by side. Next, select an Earth science variable you want to investigate, such as surface temperature, rainfall, soil moisture, or evapotranspiration. The platform fetches historical satellite records, removes recurring seasonal patterns, and runs statistical tests to evaluate whether the trend is truly meaningful. It also pairs related variables, like rainfall and soil moisture, to help explain the physical cause behind what is happening on the ground.

The frontend is built with Next.js, Tailwind CSS, Leaflet, and Plotly. The backend runs on Python and FastAPI, handling statistical calculations and pulling data directly from NASA GLDAS, NOAA Climate at a Glance, and NASA Giovanni, with cached results stored in Supabase.

To run the project locally, install the Python dependencies from requirements.txt and start the backend using uvicorn api.index:app --reload --port 8000. In another terminal, navigate into the Frontend folder, install the packages with npm install, and start the development server with npm run dev. You can then view the app at http://localhost:3000.
