import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  // 环境变量配置
  envPrefix: 'VITE_',
  // 开发服务器配置
  server: {
    host: true, // 允许外部访问
    port: 5173,
    cors: true
  },
  // 预览服务器配置
  preview: {
    host: true,
    port: 4173,
    cors: true
  }
})
