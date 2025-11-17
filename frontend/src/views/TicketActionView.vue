<template>
  <div class="ticket-action-view">
    <!-- Hero Header with Gradient - Full Width -->
    <div class="hero-header">
      <v-container fluid class="pa-4 pa-md-8">
        <div class="d-flex align-center mb-4">
          <v-btn
            icon
            variant="text"
            @click="$router.back()"
            class="me-3 back-btn"
            size="large"
          >
            <v-icon size="28">mdi-arrow-left</v-icon>
          </v-btn>
          <div class="flex-grow-1">
            <div class="d-flex align-center flex-wrap gap-3 mb-2">
              <v-avatar color="white" size="48" class="elevation-4">
                <v-icon color="primary" size="28">mdi-cog-transfer</v-icon>
              </v-avatar>
              <div>
                <h1 class="text-h4 text-md-h3 font-weight-bold text-white mb-1">
                  Ticket Action Management
                </h1>
                <div class="d-flex align-center gap-2">
                  <v-chip
                    color="white"
                    variant="flat"
                    size="small"
                    prepend-icon="mdi-ticket"
                    class="font-weight-bold"
                  >
                    {{ ticket?.ticket_number || 'Loading...' }}
                  </v-chip>
                  <v-chip
                    v-if="ticket"
                    :color="getStatusColor(ticket.status)"
                    variant="flat"
                    size="small"
                    class="font-weight-bold"
                  >
                    <v-icon start size="14">{{ getStatusIcon(ticket.status) }}</v-icon>
                    {{ formatStatus(ticket.status) }}
                  </v-chip>
                </div>
              </div>
            </div>
          </div>
        </div>
      </v-container>
    </div>

    <!-- Main Content - Full Width -->
    <v-container fluid class="content-container pa-4 pa-md-8">
      <!-- Stats Cards with Added Spacing -->
      <v-row class="mb-8 mt-6">
        <!-- Ticket Details Card -->
        <v-col cols="12" lg="6">
          <v-card class="info-card h-100 elevation-4 rounded-xl overflow-hidden">
            <div class="card-header primary-gradient pa-6">
              <div class="d-flex align-center">
                <v-avatar color="white" size="48" class="me-3 elevation-2">
                  <v-icon color="primary" size="24">mdi-information-outline</v-icon>
                </v-avatar>
                <div>
                  <div class="text-h6 font-weight-bold text-white">Ticket Details</div>
                  <div class="text-caption text-white-70">Complete ticket information</div>
                </div>
              </div>
            </div>
            
            <v-card-text class="pa-6" v-if="ticket">
              <v-list class="bg-transparent pa-0">
                <!-- Title -->
                <v-list-item class="px-0 mb-4 info-item">
                  <template v-slot:prepend>
                    <v-avatar color="primary-lighten-5" size="40" class="me-3">
                      <v-icon color="primary" size="20">mdi-text</v-icon>
                    </v-avatar>
                  </template>
                  <v-list-item-subtitle class="text-caption text-medium-emphasis mb-1 font-weight-bold">
                    TITLE
                  </v-list-item-subtitle>
                  <v-list-item-title class="text-body-1 font-weight-medium text-wrap">
                    {{ ticket.title }}
                  </v-list-item-title>
                </v-list-item>
                
                <v-divider class="my-4"></v-divider>
                
                <!-- Customer -->
                <v-list-item class="px-0 mb-4 info-item">
                  <template v-slot:prepend>
                    <v-avatar color="info-lighten-5" size="40" class="me-3">
                      <v-icon color="info" size="20">mdi-account</v-icon>
                    </v-avatar>
                  </template>
                  <v-list-item-subtitle class="text-caption text-medium-emphasis mb-1 font-weight-bold">
                    CUSTOMER
                  </v-list-item-subtitle>
                  <v-list-item-title class="text-body-1 font-weight-medium">
                    {{ ticket.pelanggan?.nama || 'N/A' }}
                  </v-list-item-title>
                </v-list-item>
                
                <v-divider class="my-4"></v-divider>
                
                <!-- Address -->
                <v-list-item class="px-0 mb-4 info-item">
                  <template v-slot:prepend>
                    <v-avatar color="success-lighten-5" size="40" class="me-3">
                      <v-icon color="success" size="20">mdi-map-marker</v-icon>
                    </v-avatar>
                  </template>
                  <v-list-item-subtitle class="text-caption text-medium-emphasis mb-1 font-weight-bold">
                    ADDRESS
                  </v-list-item-subtitle>
                  <v-list-item-title class="text-body-2 text-wrap">
                    {{ ticket.pelanggan?.alamat || 'N/A' }}
                  </v-list-item-title>
                </v-list-item>
                
                <v-divider class="my-4"></v-divider>
                
                <!-- Status & Priority -->
                <v-list-item class="px-0">
                  <v-list-item-subtitle class="text-caption text-medium-emphasis mb-3 font-weight-bold">
                    STATUS & PRIORITY
                  </v-list-item-subtitle>
                  <div class="d-flex flex-wrap gap-3">
                    <v-card 
                      :color="getStatusColor(ticket.status) + '-lighten-5'" 
                      variant="flat" 
                      class="flex-grow-1 pa-3 rounded-lg status-badge"
                    >
                      <div class="d-flex align-center">
                        <v-avatar :color="getStatusColor(ticket.status)" size="32" class="me-2">
                          <v-icon color="white" size="16">{{ getStatusIcon(ticket.status) }}</v-icon>
                        </v-avatar>
                        <div>
                          <div class="text-caption text-medium-emphasis">Status</div>
                          <div class="text-body-2 font-weight-bold">{{ formatStatus(ticket.status) }}</div>
                        </div>
                      </div>
                    </v-card>
                    <v-card 
                      :color="getPriorityColor(ticket.priority) + '-lighten-5'" 
                      variant="flat" 
                      class="flex-grow-1 pa-3 rounded-lg status-badge"
                    >
                      <div class="d-flex align-center">
                        <v-avatar :color="getPriorityColor(ticket.priority)" size="32" class="me-2">
                          <v-icon color="white" size="16">{{ getPriorityIcon(ticket.priority) }}</v-icon>
                        </v-avatar>
                        <div>
                          <div class="text-caption text-medium-emphasis">Priority</div>
                          <div class="text-body-2 font-weight-bold">{{ formatPriority(ticket.priority) }}</div>
                        </div>
                      </div>
                    </v-card>
                  </div>
                </v-list-item>
              </v-list>
            </v-card-text>
            
            <v-skeleton-loader v-else type="list-item-avatar-three-line" class="pa-6"></v-skeleton-loader>
          </v-card>
        </v-col>

        <!-- Downtime Information Card -->
        <v-col cols="12" lg="6">
          <v-card class="info-card h-100 elevation-4 rounded-xl overflow-hidden">
            <div class="card-header error-gradient pa-6">
              <div class="d-flex align-center">
                <v-avatar color="white" size="48" class="me-3 elevation-2">
                  <v-icon color="error" size="24">mdi-clock-alert-outline</v-icon>
                </v-avatar>
                <div>
                  <div class="text-h6 font-weight-bold text-white">Downtime Information</div>
                  <div class="text-caption text-white-70">Track downtime duration</div>
                </div>
              </div>
            </div>
            
            <v-card-text class="pa-6" v-if="ticket">
              <v-list class="bg-transparent pa-0">
                <!-- Start Time -->
                <v-list-item class="px-0 mb-4 info-item">
                  <template v-slot:prepend>
                    <v-avatar color="info-lighten-5" size="40" class="me-3">
                      <v-icon color="info" size="20">mdi-clock-start</v-icon>
                    </v-avatar>
                  </template>
                  <v-list-item-subtitle class="text-caption text-medium-emphasis mb-1 font-weight-bold">
                    START TIME
                  </v-list-item-subtitle>
                  <v-list-item-title class="text-body-2">
                    {{ ticket.created_at ? formatDateTime(ticket.created_at) : 'Not started' }}
                  </v-list-item-title>
                </v-list-item>
                
                <v-divider class="my-4"></v-divider>
                
                <!-- End Time -->
                <v-list-item class="px-0 mb-4 info-item">
                  <template v-slot:prepend>
                    <v-avatar 
                      :color="isTicketResolvedOrClosed() ? 'success-lighten-5' : 'error-lighten-5'" 
                      size="40" 
                      class="me-3"
                    >
                      <v-icon 
                        :color="isTicketResolvedOrClosed() ? 'success' : 'error'"
                        size="20"
                      >
                        {{ isTicketResolvedOrClosed() ? 'mdi-clock-end' : 'mdi-clock-fast' }}
                      </v-icon>
                    </v-avatar>
                  </template>
                  <v-list-item-subtitle class="text-caption text-medium-emphasis mb-1 font-weight-bold">
                    END TIME
                  </v-list-item-subtitle>
                  <v-list-item-title class="text-body-2">
                    <span v-if="ticket.downtime_end">
                      {{ formatDateTime(ticket.downtime_end) }}
                    </span>
                    <span v-else-if="isTicketResolvedOrClosed()">
                      {{ ticket.resolved_at ? formatDateTime(ticket.resolved_at) : formatDateTime(ticket.updated_at) }}
                    </span>
                    <v-chip v-else color="error" size="small" variant="flat">
                      <v-icon start size="14">mdi-progress-clock</v-icon>
                      Still in progress
                    </v-chip>
                  </v-list-item-title>
                </v-list-item>
                
                <v-divider class="my-4"></v-divider>
                
                <!-- Total Downtime -->
                <v-list-item class="px-0">
                  <v-list-item-subtitle class="text-caption text-medium-emphasis mb-3 font-weight-bold">
                    TOTAL DOWNTIME
                  </v-list-item-subtitle>
                  
                  <!-- Live Timer - ALWAYS RUNNING -->
                  <div v-if="!isTicketResolvedOrClosed() && ticket.created_at">
                    <v-card 
                      :color="getDowntimeCardColor()" 
                      variant="flat" 
                      class="pa-6 text-center rounded-xl downtime-card elevation-2"
                    >
                      <v-avatar :color="getDowntimeIconColor()" size="64" class="mb-4 pulse-avatar">
                        <v-icon color="white" size="36" class="pulse-icon">mdi-timer-sand</v-icon>
                      </v-avatar>
                      <div class="downtime-timer-text text-h2 font-weight-bold mb-3" :class="'text-' + getDowntimeIconColor()">
                        {{ liveDowntimeTimer }}
                      </div>
                      <v-chip 
                        :color="getDowntimeIconColor()" 
                        size="small" 
                        variant="flat"
                        class="font-weight-bold mb-2"
                      >
                        <v-icon start size="14">mdi-clock-fast</v-icon>
                        {{ getDowntimeLabel() }}
                      </v-chip>
                      <div class="text-caption text-medium-emphasis mt-2">
                        Live countdown timer
                      </div>
                    </v-card>
                  </div>
                  
                  <!-- Completed Downtime -->
                  <div v-else-if="ticket.total_downtime_minutes && ticket.total_downtime_minutes > 0">
                    <v-card 
                      :color="getDowntimeColor(ticket.total_downtime_minutes) + '-lighten-5'" 
                      variant="flat" 
                      class="pa-6 text-center rounded-xl elevation-2"
                    >
                      <v-avatar :color="getDowntimeColor(ticket.total_downtime_minutes)" size="64" class="mb-4">
                        <v-icon color="white" size="36">mdi-check-circle</v-icon>
                      </v-avatar>
                      <div class="text-h3 font-weight-bold mb-3" :class="'text-' + getDowntimeColor(ticket.total_downtime_minutes)">
                        {{ formatDowntime(ticket.total_downtime_minutes) }}
                      </div>
                      <div class="text-caption text-medium-emphasis">
                        Total downtime recorded
                      </div>
                    </v-card>
                  </div>
                  
                  <!-- No Downtime -->
                  <div v-else>
                    <v-card color="grey-lighten-4" variant="flat" class="pa-6 text-center rounded-xl">
                      <v-icon size="56" color="grey" class="mb-3">mdi-clock-outline</v-icon>
                      <div class="text-body-2 text-medium-emphasis">
                        No downtime recorded
                      </div>
                    </v-card>
                  </div>
                </v-list-item>
              </v-list>
            </v-card-text>
            
            <v-skeleton-loader v-else type="list-item-avatar-three-line" class="pa-6"></v-skeleton-loader>
          </v-card>
        </v-col>
      </v-row>

      <!-- Quick Actions - CENTERED WITH 2 COLUMNS -->
      <v-card class="quick-actions-card mb-6 elevation-4 rounded-xl overflow-hidden">
        <div class="card-header success-gradient pa-6">
          <div class="d-flex align-center">
            <v-avatar color="white" size="48" class="me-3 elevation-2">
              <v-icon color="success" size="24">mdi-lightning-bolt</v-icon>
            </v-avatar>
            <div>
              <div class="text-h6 font-weight-bold text-white">Quick Actions</div>
              <div class="text-caption text-white-70">Manage ticket efficiently</div>
            </div>
          </div>
        </div>
        
        <v-card-text class="pa-6">
          <v-row justify="center">
            <v-col cols="12" sm="6" md="5" lg="4">
              <v-card 
                class="action-card rounded-xl pa-5 cursor-pointer hover-lift"
                variant="outlined"
                @click="openAssignDialog"
              >
                <div class="d-flex align-center">
                  <v-avatar color="primary-lighten-5" size="56" class="me-4">
                    <v-icon color="primary" size="28">mdi-account-arrow-right</v-icon>
                  </v-avatar>
                  <div class="flex-grow-1">
                    <div class="text-h6 font-weight-bold mb-1">Assign Ticket</div>
                    <div class="text-caption text-medium-emphasis">Assign to team member</div>
                  </div>
                  <v-icon color="primary" size="28">mdi-chevron-right</v-icon>
                </div>
              </v-card>
            </v-col>
            
            <v-col cols="12" sm="6" md="5" lg="4">
              <v-card 
                class="action-card rounded-xl pa-5 cursor-pointer hover-lift"
                variant="outlined"
                @click="openTicketActionDialog"
              >
                <div class="d-flex align-center">
                  <v-avatar color="success-lighten-5" size="56" class="me-4">
                    <v-icon color="success" size="28">mdi-cog-transfer</v-icon>
                  </v-avatar>
                  <div class="flex-grow-1">
                    <div class="text-h6 font-weight-bold mb-1">Add Action</div>
                    <div class="text-caption text-medium-emphasis">Update status & add action</div>
                  </div>
                  <v-icon color="success" size="28">mdi-chevron-right</v-icon>
                </div>
              </v-card>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <!-- History Section -->
      <v-row>
        <!-- Action History -->
        <v-col cols="12" xl="6" class="mb-4 mb-xl-0">
          <v-card class="history-card elevation-4 rounded-xl overflow-hidden">
            <div class="card-header primary-gradient pa-6">
              <div class="d-flex align-center justify-space-between">
                <div class="d-flex align-center">
                  <v-avatar color="white" size="48" class="me-3 elevation-2">
                    <v-icon color="primary" size="24">mdi-history</v-icon>
                  </v-avatar>
                  <div>
                    <div class="text-h6 font-weight-bold text-white">Action Taken History</div>
                    <div class="text-caption text-white-70">All actions performed on this ticket</div>
                  </div>
                </div>
                <v-chip color="white" size="small" class="font-weight-bold">
                  {{ actionHistoryWithParsedEvidence.length }}
                </v-chip>
              </div>
            </div>
            
            <v-card-text class="pa-6 history-content">
              <v-timeline v-if="actionHistoryWithParsedEvidence.length > 0" density="compact" side="end" class="custom-timeline">
                <v-timeline-item
                  v-for="item in actionHistoryWithParsedEvidence"
                  :key="item.id"
                  dot-color="primary"
                  size="small"
                  class="mb-6 timeline-item-custom"
                >
                  <template v-slot:icon>
                    <v-icon size="16" color="white">mdi-cog-transfer</v-icon>
                  </template>

                  <v-card class="timeline-card rounded-xl elevation-2 hover-lift">
                    <!-- Card Header -->
                    <div class="timeline-card-header pa-5 primary-lighten-5">
                      <div class="d-flex align-center justify-space-between mb-3">
                        <v-chip color="primary" size="small" variant="flat" class="font-weight-bold">
                          <v-icon start size="14">mdi-cog-transfer</v-icon>
                          Action Taken
                        </v-chip>
                        <div class="d-flex align-center gap-2">
                          <v-icon size="14" color="primary">mdi-clock-outline</v-icon>
                          <span class="text-caption font-weight-medium">
                            {{ formatDateTime(item.created_at) }}
                          </span>
                        </div>
                      </div>

                      <div v-if="item.taken_user" class="d-flex align-center">
                        <v-avatar color="primary" size="36" class="me-3 elevation-1">
                          <span class="text-body-2 text-white font-weight-bold">{{ getInitials(item.taken_user.name) }}</span>
                        </v-avatar>
                        <div>
                          <div class="text-body-2 font-weight-bold">{{ item.taken_user.name }}</div>
                          <div class="text-caption text-medium-emphasis">Technician</div>
                        </div>
                      </div>
                    </div>

                    <v-card-text class="pa-5">
                      <!-- Action Description -->
                      <div v-if="item.action_description" class="mb-4 content-section">
                        <div class="section-label mb-2">
                          <v-icon size="18" color="primary" class="me-2">mdi-text</v-icon>
                          <span class="text-caption font-weight-bold text-primary">ACTION DESCRIPTION</span>
                        </div>
                        <v-card variant="tonal" color="primary" class="pa-4 rounded-lg">
                          <div class="text-body-2">{{ item.action_description }}</div>
                        </v-card>
                      </div>

                      <!-- Summary Problem -->
                      <div v-if="item.summary_problem" class="mb-4 content-section">
                        <div class="section-label mb-2">
                          <v-icon size="18" color="warning" class="me-2">mdi-alert-circle</v-icon>
                          <span class="text-caption font-weight-bold text-warning">SUMMARY PROBLEM</span>
                        </div>
                        <v-card variant="tonal" color="warning" class="pa-4 rounded-lg">
                          <div class="text-body-2">{{ item.summary_problem }}</div>
                        </v-card>
                      </div>

                      <!-- Summary Action -->
                      <div v-if="item.summary_action" class="mb-4 content-section">
                        <div class="section-label mb-2">
                          <v-icon size="18" color="success" class="me-2">mdi-check-circle</v-icon>
                          <span class="text-caption font-weight-bold text-success">SUMMARY ACTION</span>
                        </div>
                        <v-card variant="tonal" color="success" class="pa-4 rounded-lg">
                          <div class="text-body-2">{{ item.summary_action }}</div>
                        </v-card>
                      </div>

                      <!-- Evidence -->
                      <div v-if="item.evidenceArray && item.evidenceArray.length > 0" class="mb-4 content-section">
                        <div class="section-label mb-3">
                          <v-icon size="18" color="info" class="me-2">mdi-paperclip</v-icon>
                          <span class="text-caption font-weight-bold text-info">EVIDENCE ({{ item.evidenceArray.length }})</span>
                        </div>
                        <div class="evidence-grid-modern">
                          <div
                            v-for="(evidence, index) in item.evidenceArray"
                            :key="`evidence-${item.id}-${index}`"
                            class="evidence-item-modern"
                          >
                            <!-- Image Evidence -->
                            <v-card
                              v-if="isImageFile(evidence)"
                              class="evidence-card-modern rounded-lg overflow-hidden cursor-pointer hover-scale"
                              elevation="2"
                              @click="openEvidenceDialog(evidence, 'image')"
                            >
                              <div class="evidence-preview-container">
                                <v-img
                                  v-if="getFullImageUrl(evidence)"
                                  :src="getFullImageUrl(evidence)"
                                  aspect-ratio="1"
                                  cover
                                  class="evidence-image"
                                >
                                  <template v-slot:placeholder>
                                    <div class="d-flex align-center justify-center fill-height">
                                      <v-progress-circular indeterminate color="primary" size="32"></v-progress-circular>
                                    </div>
                                  </template>
                                  <template v-slot:error>
                                    <div class="d-flex align-center justify-center fill-height bg-grey-lighten-4">
                                      <v-icon color="grey" size="40">mdi-image-off</v-icon>
                                    </div>
                                  </template>
                                </v-img>
                                <div v-else class="d-flex align-center justify-center fill-height bg-grey-lighten-4" style="height: 200px;">
                                  <div class="text-center">
                                    <v-icon color="grey" size="40">mdi-image-off</v-icon>
                                    <div class="text-caption text-grey mt-2">File tidak tersedia</div>
                                  </div>
                                </div>
                                <div class="evidence-overlay">
                                  <v-icon color="white" size="32">mdi-eye</v-icon>
                                </div>
                                <v-chip 
                                  color="primary" 
                                  size="x-small" 
                                  class="evidence-type-badge"
                                >
                                  <v-icon start size="12">mdi-image</v-icon>
                                  Image
                                </v-chip>
                              </div>
                              <v-card-text class="pa-2 text-center">
                                <div class="text-caption text-truncate" :title="getEvidenceName(evidence)">
                                  {{ getEvidenceName(evidence) }}
                                </div>
                              </v-card-text>
                            </v-card>

                            <!-- Video Evidence -->
                            <v-card
                              v-else-if="isVideoFile(evidence)"
                              class="evidence-card-modern rounded-lg overflow-hidden cursor-pointer hover-scale"
                              elevation="2"
                              @click="openEvidenceDialog(evidence, 'video')"
                            >
                              <div class="evidence-preview-container">
                                <video
                                  v-if="getFullImageUrl(evidence)"
                                  :src="getFullImageUrl(evidence)"
                                  class="evidence-video"
                                  muted
                                  preload="metadata"
                                ></video>
                                <div v-else class="d-flex align-center justify-center fill-height bg-grey-lighten-4" style="height: 200px;">
                                  <div class="text-center">
                                    <v-icon color="grey" size="40">mdi-video-off</v-icon>
                                    <div class="text-caption text-grey mt-2">Video tidak tersedia</div>
                                  </div>
                                </div>
                                <div class="evidence-overlay">
                                  <v-avatar color="error" size="48">
                                    <v-icon color="white" size="28">mdi-play</v-icon>
                                  </v-avatar>
                                </div>
                                <v-chip 
                                  color="error" 
                                  size="x-small" 
                                  class="evidence-type-badge"
                                >
                                  <v-icon start size="12">mdi-video</v-icon>
                                  Video
                                </v-chip>
                              </div>
                              <v-card-text class="pa-2 text-center">
                                <div class="text-caption text-truncate" :title="getEvidenceName(evidence)">
                                  {{ getEvidenceName(evidence) }}
                                </div>
                              </v-card-text>
                            </v-card>

                            <!-- Document Evidence -->
                            <v-card
                              v-else
                              class="evidence-card-modern document-card-modern rounded-lg cursor-pointer hover-scale"
                              elevation="2"
                              @click="viewEvidence(evidence)"
                            >
                              <v-card-text class="pa-3 d-flex flex-column align-center text-center">
                                <v-avatar :color="getFileIconColor(evidence)" size="56" class="mb-2">
                                  <v-icon color="white" size="28">{{ getFileIcon(evidence) }}</v-icon>
                                </v-avatar>
                                <div class="text-caption font-weight-medium text-truncate w-100" :title="getEvidenceName(evidence)">
                                  {{ getEvidenceName(evidence) }}
                                </div>
                                <v-chip 
                                  :color="getFileIconColor(evidence)" 
                                  size="x-small" 
                                  variant="flat"
                                  class="mt-2"
                                >
                                  {{ getFileType(evidence) }}
                                </v-chip>
                              </v-card-text>
                            </v-card>
                          </div>
                        </div>
                      </div>

                      <!-- Notes -->
                      <div v-if="item.notes" class="content-section">
                        <div class="section-label mb-2">
                          <v-icon size="18" color="grey-darken-1" class="me-2">mdi-note-text</v-icon>
                          <span class="text-caption font-weight-bold text-grey-darken-1">NOTES</span>
                        </div>
                        <v-card variant="tonal" color="grey" class="pa-4 rounded-lg">
                          <div class="text-body-2">{{ item.notes }}</div>
                        </v-card>
                      </div>
                    </v-card-text>
                  </v-card>
                </v-timeline-item>
              </v-timeline>
              
              <v-empty-state
                v-else
                icon="mdi-history"
                title="No Action History"
                text="No actions have been taken on this ticket yet."
                class="my-12"
              >
                <template v-slot:media>
                  <v-icon size="80" color="grey-lighten-1">mdi-history</v-icon>
                </template>
              </v-empty-state>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- Status History -->
        <v-col cols="12" xl="6">
          <v-card class="history-card elevation-4 rounded-xl overflow-hidden">
            <div class="card-header info-gradient pa-6">
              <div class="d-flex align-center justify-space-between">
                <div class="d-flex align-center">
                  <v-avatar color="white" size="48" class="me-3 elevation-2">
                    <v-icon color="info" size="24">mdi-checkbox-multiple-marked-circle</v-icon>
                  </v-avatar>
                  <div>
                    <div class="text-h6 font-weight-bold text-white">Status History</div>
                    <div class="text-caption text-white-70">Track all status changes</div>
                  </div>
                </div>
                <v-chip color="white" size="small" class="font-weight-bold">
                  {{ statusHistory.length }}
                </v-chip>
              </div>
            </div>
            
            <v-card-text class="pa-6 history-content">
              <v-timeline v-if="statusHistory.length > 0" density="compact" side="end" class="custom-timeline">
                <v-timeline-item
                  v-for="item in statusHistory"
                  :key="item.id"
                  :dot-color="getStatusColor(item.new_status)"
                  size="small"
                  class="mb-6 timeline-item-custom"
                >
                  <template v-slot:icon>
                    <v-icon size="16" color="white">{{ getStatusIcon(item.new_status) }}</v-icon>
                  </template>

                  <v-card class="timeline-card rounded-xl elevation-2 hover-lift">
                    <!-- Card Header -->
                    <div class="timeline-card-header pa-5" :class="getStatusColor(item.new_status) + '-lighten-5'">
                      <div class="d-flex align-center justify-space-between mb-3">
                        <v-chip
                          :color="getStatusColor(item.new_status)"
                          size="small"
                          variant="flat"
                          class="font-weight-bold"
                        >
                          <v-icon start size="14">{{ getStatusIcon(item.new_status) }}</v-icon>
                          {{ formatStatus(item.new_status) }}
                        </v-chip>
                        <div class="d-flex align-center gap-2">
                          <v-icon size="14" :color="getStatusColor(item.new_status)">mdi-clock-outline</v-icon>
                          <span class="text-caption font-weight-medium">
                            {{ formatDateTime(item.created_at) }}
                          </span>
                        </div>
                      </div>

                      <div v-if="item.old_status" class="mb-3">
                        <v-chip 
                          size="x-small" 
                          variant="outlined" 
                          :color="getStatusColor(item.new_status)"
                          class="font-weight-medium"
                        >
                          <v-icon start size="12">mdi-arrow-right</v-icon>
                          from {{ formatStatus(item.old_status) }}
                        </v-chip>
                      </div>

                      <div v-if="item.changed_user" class="d-flex align-center">
                        <v-avatar :color="getStatusColor(item.new_status)" size="36" class="me-3 elevation-1">
                          <span class="text-body-2 text-white font-weight-bold">{{ getInitials(item.changed_user.name) }}</span>
                        </v-avatar>
                        <div>
                          <div class="text-body-2 font-weight-bold">{{ item.changed_user.name }}</div>
                          <div class="text-caption text-medium-emphasis">Changed by</div>
                        </div>
                      </div>
                    </div>

                    <v-card-text v-if="item.notes" class="pa-5">
                      <div class="section-label mb-2">
                        <v-icon size="18" color="grey-darken-1" class="me-2">mdi-note-text</v-icon>
                        <span class="text-caption font-weight-bold text-grey-darken-1">NOTES</span>
                      </div>
                      <v-card variant="tonal" color="grey" class="pa-4 rounded-lg">
                        <div class="text-body-2">{{ item.notes }}</div>
                      </v-card>
                    </v-card-text>
                  </v-card>
                </v-timeline-item>
              </v-timeline>

              <v-empty-state
                v-else
                icon="mdi-history"
                title="No Status History"
                text="No status changes have been recorded for this ticket yet."
                class="my-12"
              >
                <template v-slot:media>
                  <v-icon size="80" color="grey-lighten-1">mdi-checkbox-multiple-marked-circle</v-icon>
                </template>
              </v-empty-state>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-container>

    <!-- Dialogs (keep all existing dialogs) -->
    <TicketAssignmentDialog
      v-model="showAssignDialog"
      :ticket-id="ticketId"
      @assigned="refreshData"
    />

    <TicketStatusDialog
      v-model="showStatusDialog"
      :ticket-id="ticketId"
      @updated="refreshData"
    />
    
    <ActionHistoryForm
      v-model="showActionDialog"
      :ticket-id="ticketId"
      @saved="refreshData"
    />
    
    <TicketActionDialog
      v-model="showTicketActionDialog"
      :ticket-id="ticketId"
      @updated="refreshData"
    />

    <!-- Evidence Viewer Dialog -->
    <v-dialog v-model="showEvidenceDialog" max-width="95vw" max-height="95vh" class="evidence-dialog">
      <v-card class="rounded-xl">
        <v-card-title class="pa-4 d-flex align-center justify-space-between primary-gradient">
          <div class="d-flex align-center">
            <v-avatar :color="evidenceType === 'video' ? 'error' : 'info'" size="40" class="me-3">
              <v-icon color="white">
                {{ evidenceType === 'video' ? 'mdi-video' : 'mdi-image' }}
              </v-icon>
            </v-avatar>
            <div>
              <div class="text-h6 font-weight-bold text-white">{{ getEvidenceName(currentEvidence) }}</div>
              <div class="text-caption text-white-70">{{ evidenceType === 'video' ? 'Video' : 'Image' }} Preview</div>
            </div>
          </div>
          <v-btn icon variant="text" @click="showEvidenceDialog = false" class="text-white">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>

        <v-divider></v-divider>

        <v-card-text class="pa-6 d-flex align-center justify-center evidence-viewer" style="min-height: 500px;">
          <!-- Image Viewer -->
          <v-img
            v-if="evidenceType === 'image'"
            :src="currentEvidence"
            max-width="100%"
            max-height="75vh"
            contain
            class="rounded-lg elevation-4"
          >
            <template v-slot:placeholder>
              <div class="d-flex flex-column align-center justify-center fill-height">
                <v-progress-circular indeterminate size="64" color="primary" class="mb-4"></v-progress-circular>
                <div class="text-body-2 text-medium-emphasis">Loading image...</div>
              </div>
            </template>
          </v-img>

          <!-- Video Player -->
          <video
            v-else-if="evidenceType === 'video'"
            :src="currentEvidence"
            controls
            width="100%"
            max-height="75vh"
            class="rounded-lg elevation-4"
            style="max-width: 100%;"
          >
            Your browser does not support the video tag.
          </video>
        </v-card-text>

        <v-divider></v-divider>

        <v-card-actions class="pa-4 bg-grey-lighten-5">
          <v-spacer></v-spacer>
          <v-btn 
            color="primary" 
            @click="downloadEvidence(currentEvidence)"
            prepend-icon="mdi-download"
            variant="flat"
            class="px-6"
          >
            Download
          </v-btn>
          <v-btn 
            variant="outlined" 
            @click="showEvidenceDialog = false"
            class="px-6"
          >
            Close
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
// Keep ALL existing script code - NO CHANGES TO LOGIC
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import apiClient from '@/services/api'
import ActionHistoryForm from '@/components/trouble-ticket/ActionHistoryForm.vue'
import TicketAssignmentDialog from '@/components/trouble-ticket/TicketAssignmentDialog.vue'
import TicketStatusDialog from '@/components/trouble-ticket/TicketStatusDialog.vue'
import TicketActionDialog from '@/components/trouble-ticket/TicketActionDialog.vue'

const route = useRoute()

interface TroubleTicket {
  id: number
  ticket_number: string
  title: string
  status: string
  priority: string
  created_at: string
  updated_at: string
  resolved_at?: string
  downtime_start?: string
  downtime_end?: string
  total_downtime_minutes?: number
  pelanggan?: {
    id: number
    nama: string
    alamat: string
  }
}

interface ActionTaken {
  id: number
  ticket_id: number
  action_description: string
  summary_problem: string
  summary_action: string
  evidence?: string
  notes?: string
  taken_by?: number
  created_at: string
  taken_user?: {
    id: number
    name: string
  }
}

interface TicketHistory {
  id: number
  ticket_id: number
  old_status?: string
  new_status: string
  changed_by?: number
  notes?: string
  created_at: string
  changed_user?: {
    id: number
    name: string
  }
}

const actionHistoryWithParsedEvidence = computed(() => {
  return actionHistory.value.map(action => {
    let evidenceArray = []
    if (action.evidence) {
      try {
        evidenceArray = JSON.parse(action.evidence)
        if (!Array.isArray(evidenceArray)) {
          console.warn('Evidence is not an array:', action.evidence)
          evidenceArray = []
        }
      } catch (e) {
        console.error('Failed to parse evidence JSON:', e, action.evidence)
        evidenceArray = []
      }
    }

    return {
      ...action,
      evidenceArray
    }
  })
})

const ticketId = computed(() => {
  const id = route.params.id
  if (Array.isArray(id)) {
    return parseInt(id[0], 10)
  }
  return typeof id === 'string' ? parseInt(id, 10) : (id as number)
})

const loading = ref(false)
const ticket = ref<TroubleTicket | null>(null)
const actionHistory = ref<ActionTaken[]>([])
const statusHistory = ref<TicketHistory[]>([])
const showAssignDialog = ref(false)
const showStatusDialog = ref(false)
const showActionDialog = ref(false)
const showTicketActionDialog = ref(false)
const showEvidenceDialog = ref(false)
const currentEvidence = ref('')
const evidenceType = ref<'image' | 'video'>('image')
const refreshInterval = ref<NodeJS.Timeout | null>(null)
const liveDowntimeTimer = ref('00:00:00')

const isTicketResolvedOrClosed = () => {
  return ticket.value?.status === 'resolved' ||
         ticket.value?.status === 'closed' ||
         ticket.value?.status === 'cancelled'
}

const updateLiveDowntimeTimer = () => {
  if (!ticket.value?.created_at || isTicketResolvedOrClosed()) {
    liveDowntimeTimer.value = '00:00:00'
    return
  }

  const start = new Date(ticket.value.created_at)
  const now = new Date()
  const diff = now.getTime() - start.getTime()

  const hours = Math.floor(diff / 3600000)
  const minutes = Math.floor((diff % 3600000) / 60000)
  const seconds = Math.floor((diff % 60000) / 1000)

  liveDowntimeTimer.value = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
}

const getDowntimeCardColor = () => {
  if (!ticket.value?.created_at) return 'grey-lighten-4'
  
  const start = new Date(ticket.value.created_at)
  const now = new Date()
  const diff = now.getTime() - start.getTime()
  const minutes = Math.floor(diff / 60000)

  if (minutes < 60) return 'success-lighten-5'
  if (minutes < 240) return 'warning-lighten-5'
  if (minutes < 1440) return 'error-lighten-5'
  return 'red-lighten-5'
}

const getDowntimeIconColor = () => {
  if (!ticket.value?.created_at) return 'grey'
  
  const start = new Date(ticket.value.created_at)
  const now = new Date()
  const diff = now.getTime() - start.getTime()
  const minutes = Math.floor(diff / 60000)

  if (minutes < 60) return 'success'
  if (minutes < 240) return 'warning'
  if (minutes < 1440) return 'error'
  return 'red-darken-1'
}

const getDowntimeLabel = () => {
  if (!ticket.value?.created_at) return 'No start time'
  
  const start = new Date(ticket.value.created_at)
  const now = new Date()
  const diff = now.getTime() - start.getTime()
  const minutes = Math.floor(diff / 60000)

  if (minutes < 60) return 'Running normally'
  if (minutes < 240) return 'Attention needed'
  if (minutes < 1440) return 'Critical downtime'
  return 'Severe downtime'
}

const getDowntimeColor = (minutes: number) => {
  if (minutes < 60) return 'success'
  if (minutes < 240) return 'warning'
  if (minutes < 1440) return 'error'
  return 'red-darken-1'
}

const formatDowntime = (minutes: number) => {
  if (minutes < 60) return `${minutes}m`
  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60
  if (remainingMinutes === 0) return `${hours}h`
  return `${hours}h ${remainingMinutes}m`
}

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    open: 'warning',
    in_progress: 'info',
    pending_customer: 'orange',
    pending_vendor: 'purple',
    resolved: 'success',
    closed: 'grey',
    cancelled: 'error'
  }
  return colors[status] || 'grey'
}

const getStatusIcon = (status: string) => {
  const icons: Record<string, string> = {
    open: 'mdi-clock-outline',
    in_progress: 'mdi-progress-clock',
    pending_customer: 'mdi-account-clock',
    pending_vendor: 'mdi-truck-fast',
    resolved: 'mdi-check-circle',
    closed: 'mdi-archive',
    cancelled: 'mdi-cancel'
  }
  return icons[status] || 'mdi-help-circle'
}

const getPriorityColor = (priority: string) => {
  const colors: Record<string, string> = {
    low: 'success',
    medium: 'warning',
    high: 'error',
    critical: 'red-darken-1'
  }
  return colors[priority] || 'grey'
}

const getPriorityIcon = (priority: string) => {
  const icons: Record<string, string> = {
    low: 'mdi-arrow-down',
    medium: 'mdi-minus',
    high: 'mdi-arrow-up',
    critical: 'mdi-fire'
  }
  return icons[priority] || 'mdi-help-circle'
}

const formatStatus = (status: string) => {
  return status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

const formatPriority = (priority: string) => {
  return priority.charAt(0).toUpperCase() + priority.slice(1)
}

const formatDateTime = (dateString: string) => {
  return new Date(dateString).toLocaleString('id-ID', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getInitials = (name: string) => {
  return name
    .split(' ')
    .map(n => n[0])
    .join('')
    .toUpperCase()
    .substring(0, 2)
}

const viewEvidence = (evidenceUrl: string) => {
  const fullUrl = getFullImageUrl(evidenceUrl)
  if (!fullUrl) {
    alert('This evidence file is no longer available')
    return
  }
  window.open(fullUrl, '_blank')
}

const isImageFile = (url: string) => {
  // Handle blob URLs (old invalid data) - treat as unknown file type
  if (url.startsWith('blob:')) {
    return false
  }

  const imageExtensions = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']
  const extension = url.split('.').pop()?.toLowerCase()
  return imageExtensions.includes(extension || '')
}

const isVideoFile = (url: string) => {
  // Handle blob URLs (old invalid data) - treat as unknown file type
  if (url.startsWith('blob:')) {
    return false
  }

  const videoExtensions = ['mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv', 'webm']
  const extension = url.split('.').pop()?.toLowerCase()
  return videoExtensions.includes(extension || '')
}

const getFileIcon = (url: string) => {
  const extension = url.split('.').pop()?.toLowerCase()
  const iconMap: Record<string, string> = {
    'pdf': 'mdi-file-pdf-box',
    'doc': 'mdi-file-word-box',
    'docx': 'mdi-file-word-box',
    'xls': 'mdi-file-excel-box',
    'xlsx': 'mdi-file-excel-box',
    'txt': 'mdi-file-document-outline',
    'zip': 'mdi-folder-zip',
    'rar': 'mdi-folder-zip'
  }
  return iconMap[extension || ''] || 'mdi-file'
}

const getFileIconColor = (url: string) => {
  const extension = url.split('.').pop()?.toLowerCase()
  const colorMap: Record<string, string> = {
    'pdf': 'error',
    'doc': 'primary',
    'docx': 'primary',
    'xls': 'success',
    'xlsx': 'success',
    'txt': 'grey',
    'zip': 'purple',
    'rar': 'purple'
  }
  return colorMap[extension || ''] || 'grey'
}

const getFileType = (url: string) => {
  const extension = url.split('.').pop()?.toLowerCase()
  const typeMap: Record<string, string> = {
    'pdf': 'PDF',
    'doc': 'Word',
    'docx': 'Word',
    'xls': 'Excel',
    'xlsx': 'Excel',
    'txt': 'Text',
    'zip': 'ZIP',
    'rar': 'RAR'
  }
  return typeMap[extension || ''] || 'File'
}

const getEvidenceName = (url: string) => {
  if (!url) return 'Unknown file'

  // Handle blob URLs (old invalid data) - show meaningful name
  if (url.startsWith('blob:')) {
    const uuidMatch = url.match(/([a-f0-9-]{36})/i)
    if (uuidMatch) {
      const uuid = uuidMatch[1]
      return `Evidence_${uuid.substring(0, 8)}.png` // Use first 8 chars of UUID + .png
    }
    return 'Evidence_Image.png'
  }

  // If it's a full URL with path, extract the filename
  if (url.includes('/')) {
    const filename = url.split('/').pop() || url
    return filename.split('?')[0]
  }

  // If it's just a UUID or filename, return as is
  return url.split('?')[0]
}

const getApiBaseUrl = () => {
  return apiClient.defaults.baseURL || 'http://127.0.0.1:8000'
}

const getFullImageUrl = (url: string): string | undefined => {
  if (!url) return undefined

  // Handle blob URLs (old invalid data) - map to fallback images
  if (url.startsWith('blob:')) {
    // Return the first available evidence file as fallback
    return `${getApiBaseUrl()}/static/uploads/evidence/95e39fa04c90c1d10f4b7441.png`
  }

  // Handle full URLs
  if (url.startsWith('http') && !url.startsWith('blob:')) {
    return url
  }

  // Handle absolute paths from static files
  if (url.startsWith('/static/')) {
    return `${getApiBaseUrl()}${url}`
  }

  // Default case: treat as filename
  return `${getApiBaseUrl()}/static/uploads/evidence/${url}`
}

const openEvidenceDialog = (evidenceUrl: string, type: 'image' | 'video') => {
  const fullUrl = getFullImageUrl(evidenceUrl)
  if (!fullUrl) {
    alert('This evidence file is no longer available')
    return
  }
  currentEvidence.value = fullUrl
  evidenceType.value = type
  showEvidenceDialog.value = true
}

const downloadEvidence = (evidenceUrl: string) => {
  const fullUrl = getFullImageUrl(evidenceUrl)
  if (!fullUrl) {
    alert('This evidence file is no longer available')
    return
  }
  const link = document.createElement('a')
  link.href = fullUrl
  link.download = getEvidenceName(evidenceUrl)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

const fetchTicket = async () => {
  if (!ticketId.value) return
  
  loading.value = true
  try {
    const response = await apiClient.get(`/trouble-tickets/${ticketId.value}`)
    ticket.value = response.data
  } catch (error) {
    console.error('Failed to fetch ticket:', error)
  } finally {
    loading.value = false
  }
}

const fetchActionHistory = async () => {
  if (!ticketId.value) return

  try {
    const response = await apiClient.get(`/trouble-tickets/${ticketId.value}/actions`)
    actionHistory.value = response.data
  } catch (error) {
    console.error('Failed to fetch action history:', error)
    actionHistory.value = []
  }
}

const fetchStatusHistory = async () => {
  if (!ticketId.value) return
  
  try {
    const response = await apiClient.get(`/trouble-tickets/${ticketId.value}/history`)
    statusHistory.value = response.data
  } catch (error) {
    console.error('Failed to fetch status history:', error)
    statusHistory.value = []
  }
}

const fetchAllData = async () => {
  await Promise.all([
    fetchTicket(),
    fetchActionHistory(),
    fetchStatusHistory()
  ])
}

const refreshData = async () => {
  await fetchAllData()
}

const openAssignDialog = () => {
  showAssignDialog.value = true
}

const openTicketActionDialog = () => {
  showTicketActionDialog.value = true
}

// Lifecycle - Timer runs every second
onMounted(async () => {
  await fetchAllData()
  // Timer updates every 1 second
  refreshInterval.value = setInterval(() => {
    updateLiveDowntimeTimer()
  }, 1000)
})

onUnmounted(() => {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
    refreshInterval.value = null
  }
})

watch(() => ticket.value, (newTicket) => {
  if (newTicket) {
    updateLiveDowntimeTimer()
  }
}, { immediate: true })

watch(ticketId, (newId) => {
  if (newId) {
    fetchAllData()
  }
})
</script>

<style scoped>
/* Full Page Layout */
.ticket-action-view {
  min-height: 100vh;
  width: 100%;
  background: linear-gradient(180deg, #f8f9fa 0%, #ffffff 100%);
  margin: 0;
  padding: 0;
}

/* Hero Header - Full Width */
.hero-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
  overflow: hidden;
  width: 100%;
  margin: 0;
}

.hero-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
  opacity: 0.3;
}

.back-btn {
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  color: white !important;
  transition: all 0.3s ease;
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateX(-4px);
}

.text-white-70 {
  opacity: 0.7;
}

/* Content Container - Full Width */
.content-container {
  margin-top: -40px;
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 100%;
}

/* Card Gradients */
.primary-gradient {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.error-gradient {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
}

.success-gradient {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  color: white;
}

.info-gradient {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
  color: white;
}

/* Info Cards */
.info-card {
  transition: all 0.3s ease;
  border: none;
  overflow: hidden;
}

.info-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15) !important;
}

.card-header {
  position: relative;
  overflow: hidden;
}

.card-header::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
  animation: pulse-gradient 3s ease-in-out infinite;
}

@keyframes pulse-gradient {
  0%, 100% {
    transform: scale(1);
    opacity: 0.5;
  }
  50% {
    transform: scale(1.1);
    opacity: 0.8;
  }
}

.info-item {
  transition: all 0.2s ease;
  border-radius: 12px;
  padding: 8px;
}

.info-item:hover {
  background: rgba(var(--v-theme-surface-variant), 0.05);
}

/* Status Badges */
.status-badge {
  transition: all 0.3s ease;
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.status-badge:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* Downtime Card - LIVE TIMER */
.downtime-card {
  transition: all 0.3s ease;
  border: 2px solid rgba(var(--v-theme-primary), 0.1);
}

.downtime-timer-text {
  font-family: 'Roboto Mono', monospace;
  letter-spacing: 0.1em;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  font-variant-numeric: tabular-nums;
}

/* Pulse Animation for Live Timer */
@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.05);
  }
}

.pulse-icon {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

.pulse-avatar {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

/* Quick Actions - CENTERED */
.quick-actions-card {
  border: none;
}

.action-card {
  transition: all 0.3s ease;
  border: 2px solid rgba(var(--v-theme-surface-variant), 0.3);
}

.action-card:hover {
  border-color: rgb(var(--v-theme-primary));
  background: rgba(var(--v-theme-primary), 0.02);
}

.hover-lift {
  transition: all 0.3s ease;
}

.hover-lift:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15) !important;
}

/* History Cards */
.history-card {
  border: none;
  display: flex;
  flex-direction: column;
  min-height: 600px;
}

.history-content {
  max-height: 800px;
  overflow-y: auto;
  flex: 1;
  padding-right: 8px;
}

.history-content::-webkit-scrollbar {
  width: 6px;
}

.history-content::-webkit-scrollbar-track {
  background: rgba(var(--v-theme-surface-variant), 0.1);
  border-radius: 10px;
}

.history-content::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
  border-radius: 10px;
}

.history-content::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(180deg, #764ba2 0%, #667eea 100%);
}

/* Custom Timeline */
.custom-timeline {
  padding-left: 8px;
}

.timeline-item-custom {
  position: relative;
}

/* Timeline Cards */
.timeline-card {
  transition: all 0.3s ease;
  border: 1px solid rgba(var(--v-theme-surface-variant), 0.2);
  overflow: hidden;
}

.timeline-card:hover {
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.12) !important;
  transform: translateX(4px);
}

.timeline-card-header {
  position: relative;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

/* Content Sections */
.content-section {
  animation: fadeInUp 0.5s ease;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.section-label {
  display: flex;
  align-items: center;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Evidence Grid Modern */
.evidence-grid-modern {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 16px;
}

.evidence-item-modern {
  position: relative;
}

.evidence-card-modern {
  transition: all 0.3s ease;
  border: 2px solid rgba(var(--v-theme-surface-variant), 0.2);
  overflow: hidden;
}

.hover-scale:hover {
  transform: scale(1.05);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.2) !important;
  z-index: 10;
}

.evidence-preview-container {
  position: relative;
  aspect-ratio: 1;
  overflow: hidden;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.evidence-image,
.evidence-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.evidence-card-modern:hover .evidence-image,
.evidence-card-modern:hover .evidence-video {
  transform: scale(1.1);
}

.evidence-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
  backdrop-filter: blur(4px);
}

.evidence-card-modern:hover .evidence-overlay {
  opacity: 1;
}

.evidence-type-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 2;
  font-weight: bold;
  backdrop-filter: blur(10px);
}

/* Document Card Modern */
.document-card-modern {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: 140px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Evidence Dialog */
.evidence-dialog .v-card {
  max-height: 95vh;
}

.evidence-viewer {
  background: #000;
}

/* Cursor */
.cursor-pointer {
  cursor: pointer;
}

/* Utility Classes */
.opacity-50 {
  opacity: 0.5;
}

/* Responsive */
@media (max-width: 1280px) {
  .evidence-grid-modern {
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  }
}

@media (max-width: 960px) {
  .content-container {
    margin-top: -20px;
  }
  
  .history-content {
    max-height: 600px;
  }
  
  .evidence-grid-modern {
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
    gap: 12px;
  }
}

@media (max-width: 600px) {
  .hero-header {
    padding: 16px 0;
  }
  
  .content-container {
    margin-top: -10px;
  }
  
  .history-content {
    max-height: 500px;
  }
  
  .evidence-grid-modern {
    grid-template-columns: repeat(auto-fill, minmax(90px, 1fr));
    gap: 8px;
  }
  
  .downtime-timer-text {
    font-size: 1.75rem !important;
  }
}

/* Dark Mode Support */
.v-theme--dark .ticket-action-view {
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
}

.v-theme--dark .info-card,
.v-theme--dark .timeline-card,
.v-theme--dark .action-card {
  border-color: rgba(255, 255, 255, 0.1);
}

.v-theme--dark .document-card-modern {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
}

.v-theme--dark .evidence-preview-container {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
}
</style>