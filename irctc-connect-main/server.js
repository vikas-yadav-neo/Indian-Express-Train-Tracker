import express from "express";
import routes from "./routes/index.js";
import morgan from "morgan";
import cors from "cors";

const app = express();

app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(morgan("dev"));
app.use(cors());

app.get("/test", (req, res) => {
  return res.json({
    message: "hello api working",
  });
});

app.use("/api/train", routes);

const PORT = 3001;

app.listen(PORT, () => {
  console.log(`server is running on port ${PORT}`);
});
