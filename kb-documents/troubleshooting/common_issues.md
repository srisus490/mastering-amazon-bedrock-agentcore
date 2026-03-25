# Troubleshooting Guide

## Issue: "System not found"

**Symptoms:** User asks about a system that doesn't exist

**Solution:**
1. Check source_systems table for exact system ID
2. Suggest similar system names
3. List all available systems

**Example Response:**
"I couldn't find 'PROD_SUPPLIER' in the database. Did you mean 'PROD_ANALYTICS'? Here are all available systems: PROD_ANALYTICS, PROD_SALES, PROD_INVENTORY, TEST001"

## Issue: "No data for date range"

**Symptoms:** Query returns empty results

**Solution:**
1. Verify date range is valid
2. Check if system was active during that period
3. Suggest alternative date ranges

**Example Response:**
"I don't see any data for PROD_ANALYTICS between 2025-01-01 and 2025-01-05. This system may not have been active then. Would you like to see data from the last 7 days instead?"

## Issue: "Ambiguous question"

**Symptoms:** User question could mean multiple things

**Solution:**
1. Ask clarifying questions
2. Provide options
3. Suggest specific queries

**Example Response:**
"When you ask 'how is it doing?', do you mean:
1. File arrival status today?
2. SLA compliance this week?
3. Trend over the last month?
Please let me know which you'd like to see."

## Issue: "Complex query timeout"

**Symptoms:** Query takes too long to execute

**Solution:**
1. Suggest narrower date range
2. Focus on single system
3. Use aggregated data

**Example Response:**
"That query might take a while. Let me narrow it down - would you like to see data for just one system, or a shorter time period?"
