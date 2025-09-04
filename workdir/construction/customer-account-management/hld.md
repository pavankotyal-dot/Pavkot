# Customer & Account Management Unit - High Level Design

## Overview
The Customer & Account Management Unit handles the complete customer lifecycle from registration through account management, including tier status visibility and communication preferences.

## Business Capabilities
- Customer registration and profile management
- Program onboarding and education
- Tier status tracking and display
- Communication preference management

## Strategic Components

### 1. Customer Registration Service
**Responsibility:** Handle new customer registration and account creation
**Key Functions:**
- Validate customer information and card details
- Create customer profile with Bronze tier assignment
- Initialize customer preferences
- Trigger welcome workflows

### 2. Onboarding Service
**Responsibility:** Guide customers through program education and setup
**Key Functions:**
- Deliver interactive tutorial content
- Track onboarding progress and completion
- Generate personalized recommendations
- Configure initial engagement preferences

### 3. Profile Management Service
**Responsibility:** Manage customer profile information and preferences
**Key Functions:**
- Update customer personal information
- Manage communication preferences (email, SMS, push, in-app)
- Handle preference validation and storage
- Maintain profile history and audit trail

### 4. Tier Status Display Service
**Responsibility:** Provide read-only tier status information to customers
**Key Functions:**
- Retrieve current tier status from Transaction Engine
- Display tier benefits and privileges
- Show progress toward next tier
- Present tier maintenance requirements

## Data Components

### Customer Profile Database
- Customer personal information
- Registration status and timestamps
- Communication preferences
- Profile update history

### Onboarding Progress Store
- Tutorial completion status
- Onboarding step tracking
- Personalization data
- Engagement metrics

## Integration Components

### External System Connectors
- **Card Validation Service Adapter:** Validate customer card information
- **Identity Verification Adapter:** Verify customer identity and eligibility
- **Email Service Connector:** Send registration confirmations and communications
- **SMS Service Connector:** Send SMS notifications and alerts

### Internal System Integrations
- **Transaction Engine Client:** Retrieve tier status and spending data
- **Analytics Engine Client:** Send customer behavior data
- **Event Publisher:** Publish customer lifecycle events

## Communication Components

### REST APIs (External)
```
POST /api/v1/customers/register
GET /api/v1/customers/{customerId}/profile
PUT /api/v1/customers/{customerId}/profile
GET /api/v1/customers/{customerId}/tier-status
PUT /api/v1/customers/{customerId}/preferences
GET /api/v1/customers/{customerId}/onboarding-status
POST /api/v1/customers/{customerId}/complete-onboarding
```

### Event Handlers
- **CustomerRegistered:** Published when registration completes
- **CustomerOnboardingCompleted:** Published when onboarding finishes
- **CommunicationPreferencesUpdated:** Published when preferences change
- **TierAdvanced:** Consumed to update tier display information

### Message Queue Integration
- **Customer Events Topic:** Publish customer lifecycle events
- **Tier Updates Topic:** Subscribe to tier advancement notifications

## Observability Components

### Health Checks
- Database connectivity and response time
- External service availability (email, SMS, card validation)
- API endpoint response times
- Event publishing/consuming status

### Business Metrics
- Customer registration rate (hourly/daily)
- Onboarding completion percentage
- Communication preference update frequency
- Tier status view count

### Monitoring Integration
- **Metrics Endpoint:** `/metrics` for monitoring system integration
- **Health Endpoint:** `/health` for service status checks
- **Business Logs:** Structured logging with customer-friendly messages

## Security Components

### Authentication & Authorization
- **API Gateway Integration:** Route and authenticate external requests
- **Customer Authentication:** Validate customer identity for profile operations
- **Role-Based Access:** Ensure customers can only access their own data

### Data Protection
- **PII Encryption:** Encrypt sensitive customer information at rest
- **Data Masking:** Mask sensitive data in logs and monitoring
- **Audit Logging:** Track all profile changes and access attempts

## Component Interactions

### Registration Flow
1. Customer Registration Service validates input and creates profile
2. Profile Management Service stores customer data
3. Tier Status Display Service initializes with Bronze tier
4. Event Publisher sends CustomerRegistered event
5. Onboarding Service begins tutorial workflow

### Profile Update Flow
1. Profile Management Service validates and updates customer data
2. Security Components audit the changes
3. Event Publisher sends profile update events
4. External connectors sync changes to communication services

### Tier Status Display Flow
1. Tier Status Display Service receives tier update events
2. Service retrieves latest tier information from Transaction Engine
3. Updated tier status is cached for quick customer access
4. Observability Components log tier status views

## Scalability Considerations
- **Horizontal Scaling:** All services designed for stateless operation
- **Caching Strategy:** Tier status and profile data cached for performance
- **Database Partitioning:** Customer data partitioned by customer ID
- **Event-Driven Architecture:** Asynchronous processing for non-critical operations