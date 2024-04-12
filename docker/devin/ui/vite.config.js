import defineConfig from "./vite.config"
import os from "os"

let extConfig = {
  ...defineConfig,
  server: {
    origin: 'http://' + $(os.hostname()) + ':' + process.env.HOST_PORT,
  }
}


export default defineConfig(extConfig);
