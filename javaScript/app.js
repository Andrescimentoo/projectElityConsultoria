import express from "express";
import cors from 'cors';

const app = express()
const PORT = 5000

app.use(cors())

try {
    app.listen(PORT, () => {
        console.log("server iniciado!")
    }) 
} catch (error) {
    console.log("erro ao iniciar server", error)
};
