"use client";

import { useState } from "react";
import Navbar from "@/components/layout/Navbar";
import WorldMapAnimation from "@/components/visuals/WorldMapAnimation";
import Footer from "@/components/layout/Footer";

export default function ContactPage() {
  const [submitted, setSubmitted] = useState(false);

  return (
    <main className="relative min-h-screen flex flex-col">
      {/* World Map Background */}
      <WorldMapAnimation />

      {/* NAVBAR */}
      <Navbar />

      <div className="relative z-10 flex-grow flex flex-col items-center justify-center px-4 py-12">
        <section className="max-w-lg w-full">
          <h1 className="text-4xl font-bold mb-4 text-blue-700 text-center">Contact Us</h1>
          <p className="text-gray-700 mb-8 text-center">We&apos;d love to hear from you. Fill out the form below and we&apos;ll get back to you as soon as possible.</p>
          {!submitted ? (
            <form className="bg-white p-8 rounded shadow-md w-full space-y-6" onSubmit={e => { e.preventDefault(); setSubmitted(true); }}>
              <div>
                <label htmlFor="name" className="block text-sm font-semibold mb-1">Name</label>
                <input type="text" id="name" required className="w-full border rounded px-3 py-2 mt-1 focus:outline-none focus:ring-2 focus:ring-blue-400" />
              </div>
              <div>
                <label htmlFor="email" className="block text-sm font-semibold mb-1">Email</label>
                <input type="email" id="email" required className="w-full border rounded px-3 py-2 mt-1 focus:outline-none focus:ring-2 focus:ring-blue-400" />
              </div>
              <div>
                <label htmlFor="message" className="block text-sm font-semibold mb-1">Message</label>
                <textarea id="message" required className="w-full border rounded px-3 py-2 mt-1 h-32 resize-none focus:outline-none focus:ring-2 focus:ring-blue-400"></textarea>
              </div>
              <button type="submit" className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 font-semibold">Send Message</button>
            </form>
          ) : (
            <div className="bg-green-50 border border-green-200 text-green-900 text-center px-6 py-8 rounded shadow-md">
              <h2 className="text-2xl font-semibold mb-2">Thank you!</h2>
              <p>Your message has been received. We appreciate your interest and will contact you soon.</p>
            </div>
          )}
        </section>
      </div>

      {/* Footer */}
      <Footer />
    </main>
  );
}
