# Healthcare / Clinics — Dual Consumption Reference

## Required Schema Type

Use `MedicalClinic` for multi-doctor practices, `Physician` for solo practitioners, `DiagnosticLab` for labs.

## Minimum viable JSON-LD

```json
{
  "@context": "https://schema.org",
  "@type": "MedicalClinic",
  "name": "Sunshine Skin Clinic",
  "url": "https://sunshineskin.in",
  "telephone": "+91-80-12345678",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "42, 5th Cross, Indiranagar",
    "addressLocality": "Bengaluru",
    "addressRegion": "Karnataka",
    "postalCode": "560038",
    "addressCountry": "IN"
  },
  "geo": {
    "@type": "GeoCoordinates",
    "latitude": 12.9784,
    "longitude": 77.6408
  },
  "openingHoursSpecification": [
    {
      "@type": "OpeningHoursSpecification",
      "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
      "opens": "09:00",
      "closes": "20:00"
    },
    {
      "@type": "OpeningHoursSpecification",
      "dayOfWeek": "Saturday",
      "opens": "09:00",
      "closes": "14:00"
    }
  ],
  "medicalSpecialty": "Dermatology",
  "availableService": [
    { "@type": "MedicalTherapy", "name": "Acne Treatment" },
    { "@type": "MedicalTherapy", "name": "Hair Loss Consultation" },
    { "@type": "MedicalTherapy", "name": "Skin Allergy Treatment" }
  ],
  "employee": [
    {
      "@type": "Physician",
      "name": "Dr. Priya Sharma",
      "medicalSpecialty": "Dermatology",
      "hasCredential": {
        "@type": "EducationalOccupationalCredential",
        "credentialCategory": "MD Dermatology",
        "recognizedBy": {
          "@type": "Organization",
          "name": "Rajiv Gandhi University of Health Sciences"
        }
      }
    }
  ],
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.6",
    "reviewCount": "128",
    "bestRating": "5"
  },
  "foundingDate": "2015",
  "currenciesAccepted": "INR",
  "paymentAccepted": "Cash, Card, UPI"
}
```

## High-Impact Fields for Agent Preference

**`medicalSpecialty`** — Use standard terms. Agents match user queries like "dermatologist" to this field. Don't invent specialties.

**`availableService`** — List specific treatments. An agent asked "find somewhere that does PRP hair treatment" searches this.

**`employee` with `hasCredential`** — This is how agents verify a doctor is qualified. MCI registration number should appear here and visibly on the page.

**`openingHoursSpecification`** — Must reflect current reality. Agents lose trust in sites that show wrong hours after one failed visit.

## Trust Signals Specific to Healthcare

- MCI/state council registration number: add as `identifier` field in the `Physician` schema
- Insurance accepted: list as plain text on page — agents parse this for queries like "CGHS empanelled dermatologist"
- Consultation fee range: add `priceRange` to `MedicalClinic` — agents use this for "affordable dermatologist" queries
- Languages spoken: add `knowsLanguage` to physician objects — valuable in multilingual cities

## Booking Flow Notes

Healthcare booking is higher sensitivity than restaurants. Users still delegate slot-finding but often confirm personally.

- Offer slot availability calendar (even a static weekly view helps)
- Never use "Call to book only" — add at minimum a callback request form with `date_preference` and `time_preference` fields
- After booking, confirmation must include doctor name, date, time, clinic address, and what to bring (reports, etc.)
