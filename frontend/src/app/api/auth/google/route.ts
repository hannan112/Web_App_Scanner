// In src/app/api/auth/google/route.ts

import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // Extract token data
    const { access_token, id_token } = body;
    
    if (!access_token && !id_token) {
      console.error('Missing required tokens in request:', body);
      return NextResponse.json(
        { error: 'Missing required tokens' },
        { status: 400 }
      );
    }
    
    // Log what we're sending to the backend
    console.log('Forwarding Google tokens to backend');
    
    // Build backend API URL robustly to avoid double /api prefixes
    const rawBase = process.env.NEXT_PUBLIC_API_URL || '';
    const trimmedBase = rawBase.replace(/\/$/, ''); // remove trailing slash if present
    const apiBase = /\/api$/.test(trimmedBase) ? trimmedBase : `${trimmedBase}/api`;
    const apiUrl = `${apiBase}/auth/google/`;
    console.log('Backend API URL:', apiUrl);
    
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        access_token, 
        id_token 
      }),
    });
    
    // Get response text first for debugging
    const responseText = await response.text();
    console.log(`Backend response status: ${response.status}`);
    
    let data;
    try {
      // Try to parse as JSON if possible
      data = JSON.parse(responseText);
      console.log('Backend response parsed successfully');
    } catch (e) {
      console.error('Failed to parse backend response as JSON:', e);
      // If not JSON, use the raw text
      data = { text: responseText };
    }
    
    if (!response.ok) {
      console.error('Backend authentication failed:', data);
      return NextResponse.json(
        { error: 'Authentication failed', details: data },
        { status: response.status }
      );
    }
    
    // Ensure the response contains the expected fields
    if (!data.access) {
      console.error('Backend response missing access token:', data);
      return NextResponse.json(
        { error: 'Invalid authentication response from backend' },
        { status: 500 }
      );
    }
    
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error in Google auth API route:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}