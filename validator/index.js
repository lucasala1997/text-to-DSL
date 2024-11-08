import cors from "cors";
import dotenv from "dotenv";
import express from "express";
import parser from "@lbdudc/sensor-dsl";



dotenv.config();
dotenv.config({ path: `.env.local`, override: true });

const CLIENT_URL = process.env.CLIENT_URL || "http://localhost:5173";
const PORT = process.env.SERVER_PORT || 3000;

const app = express();

app.use(cors({ origin: CLIENT_URL, credentials: true }));
app.use(express.json());


app.post("/api/sensor/validate", (req, res) => {
    const { expected_dsl_output, generated_dsl_output } = req.body;

    if (!expected_dsl_output || !generated_dsl_output) {
        return res.json({ error: "expected_dsl_output and generated_dsl_output are required" });
    }

    let expected, generated;

    parser.reset();

    try {
        expected = parser.parse(expected_dsl_output);
    } catch (error) {
        console.log("error", error);
        return res.json({
            error: error.message,
            dsl_output_file_with_errors: "expected_dsl_output"
        });
    }

    parser.reset();

    try {
        generated = parser.parse(generated_dsl_output);
    } catch (error) {
        console.log("error", error);
        return res.json({
            error: error.message,
            dsl_output_file_with_errors: "generated_dsl_output"
        });
    }

    // check if deep equals the two objects
    res.json({
        is_valid: expected != null && generated != null && JSON.stringify(expected) === JSON.stringify(generated),
        full_output: {
            expected,
            generated
        }
    })
});

app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
