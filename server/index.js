const express = require("express");
const app = express();
const mongoose = require("mongoose");
const dotenv = require("dotenv");
const cors = require("cors");
dotenv.config();

const Review = require("./models/review-model");

app.use(express.json());
app.use(cors());

app.post("/review", async (req, res) => {
    try {
        // const { problem, solution } = req.body;
      const newEntry = new Review(req.body);
  
      const data = await newEntry.save();  // Save to MongoDB
      console.log("New problem-solution pair saved:", newEntry);
      res.json(data);
    } catch (err) {
      console.error("Error saving problem-solution pair:", err);
      throw new Error("Error");
    }});

    app.get("/getReviews", async (req, res) => {  // Change from POST to GET
        try {
            const reviews = await Review.find({});  // Fetch all reviews from MongoDB
            res.json(reviews);  // Send JSON response
        } catch (error) {
            console.error("Error fetching reviews:", error);
            res.status(500).json({ message: "Internal Server Error" });
        }
    });

mongoose
  .connect(process.env.MONGO_URI)
  .then(() => {
    console.log("Connected to MongoDB")
    app.listen(3000, () => {
        console.log("Server running at port 3000");
    })
})
  .catch((err) => console.error("MongoDB Connection Error:", err));
