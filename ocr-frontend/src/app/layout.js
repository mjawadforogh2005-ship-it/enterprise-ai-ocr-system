export const metadata = {
  title: "AI OCR System",
  description: "Enterprise Offline OCR System",
};

export default function RootLayout({ children }) {
  return (
    <html lang="fa" dir="rtl">
      <head>
        <script src="https://cdn.tailwindcss.com"></script>
      </head>
      <body className="bg-slate-950 text-slate-100">{children}</body>
    </html>
  );
}