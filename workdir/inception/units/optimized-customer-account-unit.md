# Customer & Account Management Unit

## Unit Overview
Handles complete customer lifecycle from registration through account management, including tier status visibility and communication preferences.

## Business Capability
- Customer registration and onboarding
- Account profile management
- Tier status display and tracking
- Communication preference management

## User Stories

### US001: Customer Registration
**As a** new customer  
**I want** to register for the loyalty and rewards program  
**So that** I can start earning points on my card purchases

### US002: Program Onboarding Tutorial
**As a** newly registered customer  
**I want** to understand how the rewards program works  
**So that** I can maximize my point earning potential

### US006: Tier Status Tracking
**As a** program member  
**I want** to see my current tier status and progress to the next tier  
**So that** I can understand my benefits and work towards tier advancement

### US020: Proactive Communication Preferences
**As a** program member  
**I want** to control how and when I receive program communications  
**So that** I can stay informed without being overwhelmed

## Data Ownership
- Customer profiles and personal information
- Registration and onboarding status
- Communication preferences
- Tier status display (read-only from Transaction Engine)

## Events Published
- CustomerRegistered
- CustomerOnboardingCompleted
- CommunicationPreferencesUpdated

## Events Consumed
- TierAdvanced (for status display updates)