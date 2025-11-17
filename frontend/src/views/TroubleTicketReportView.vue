<template>
  <div class="trouble-ticket-report-container">
    <!-- ===== ENHANCED HEADER SECTION ===== -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <div class="header-icon-wrapper">
            <v-avatar
              color="primary"
              size="64"
              class="header-avatar"
              elevation="8"
            >
              <v-icon size="36" color="white">mdi-chart-box-outline</v-icon>
            </v-avatar>
          </div>
          <div class="header-text">
            <h1 class="page-title">
              <span class="title-solid">Trouble Ticket Reports</span>
            </h1>
            <p class="page-subtitle">
              <v-icon size="18" class="me-2">mdi-chart-line</v-icon>
              Comprehensive analytics and insights for ticket management
            </p>
          </div>
        </div>
        <div class="header-actions">
          <v-btn
            prepend-icon="mdi-refresh"
            @click="refreshAllData"
            :loading="loading"
            size="large"
            class="modern-btn refresh-btn-modern"
            color="primary"
            variant="outlined"
            elevation="2"
            rounded="pill"
          >
            <span class="btn-text">Refresh Data</span>
          </v-btn>
          <v-btn
            prepend-icon="mdi-download"
            @click="exportReport"
            :disabled="loading || exporting"
            :loading="exporting"
            size="large"
            class="modern-btn export-btn-modern"
            color="success"
            variant="flat"
            elevation="4"
            rounded="pill"
          >
            <v-icon end class="ms-1">mdi-file-export</v-icon>
            <span class="btn-text">Export Report</span>
          </v-btn>
        </div>
      </div>
    </div>

    <!-- ===== ENHANCED DATE RANGE FILTER ===== -->
    <v-card class="date-filter-card" elevation="0">
      <v-card-text class="pa-6">
        <div class="filter-header">
          <div class="filter-title-wrapper">
            <div class="filter-icon">
              <v-icon color="primary" size="24">mdi-calendar-range</v-icon>
            </div>
            <div>
              <h3 class="filter-title">Report Period</h3>
              <p class="filter-subtitle">Select date range to filter reports</p>
            </div>
          </div>
          <v-chip
            v-if="dateRange.from || dateRange.to"
            color="primary"
            variant="flat"
            size="default"
            prepend-icon="mdi-filter-check"
            class="active-filter-chip"
          >
            Custom Range Active
          </v-chip>
        </div>

        <div class="date-range-filters">
          <v-row>
            <v-col cols="12" md="5">
              <v-text-field
                v-model="dateRange.from"
                type="date"
                label="Start Date"
                prepend-inner-icon="mdi-calendar-start"
                variant="outlined"
                density="comfortable"
                hide-details
                @update:modelValue="applyDateFilter"
                class="date-input"
              />
            </v-col>
            <v-col cols="12" md="5">
              <v-text-field
                v-model="dateRange.to"
                type="date"
                label="End Date"
                prepend-inner-icon="mdi-calendar-end"
                variant="outlined"
                density="comfortable"
                hide-details
                @update:modelValue="applyDateFilter"
                class="date-input"
              />
            </v-col>
            <v-col cols="12" md="2">
              <v-btn
                variant="outlined"
                prepend-icon="mdi-filter-remove"
                @click="clearDateFilter"
                :disabled="!dateRange.from && !dateRange.to"
                block
                size="large"
                color="error"
                class="clear-filter-btn"
              >
                Clear
              </v-btn>
            </v-col>
          </v-row>
        </div>
      </v-card-text>
    </v-card>

    <!-- ===== ENHANCED KEY METRICS OVERVIEW ===== -->
    <div class="metrics-overview">
      <div class="section-header">
        <div class="section-header-content">
          <v-icon class="section-icon" color="primary">mdi-view-dashboard-outline</v-icon>
          <div>
            <h2 class="section-title">Key Performance Metrics</h2>
            <p class="section-subtitle">Real-time overview of ticket performance</p>
          </div>
        </div>
      </div>

      <div class="metrics-grid">
        <!-- Total Tickets Card -->
        <v-card class="metric-card total-tickets-card" elevation="0">
          <div class="metric-gradient gradient-blue"></div>
          <v-card-text class="metric-content">
            <div class="metric-icon-wrapper blue-gradient">
              <v-icon size="32" color="white">mdi-ticket-outline</v-icon>
            </div>
            <div class="metric-info">
              <div class="metric-value">{{ statistics?.total_tickets || 0 }}</div>
              <div class="metric-label">Total Tickets</div>
              <div class="metric-change positive">
                <v-icon size="16">mdi-trending-up</v-icon>
                <span>All time</span>
              </div>
            </div>
          </v-card-text>
          <div class="metric-footer">
            <v-icon size="14" class="me-1">mdi-information-outline</v-icon>
            <span>Total tickets created</span>
          </div>
        </v-card>

        <!-- Resolution Rate Card -->
        <v-card class="metric-card resolution-rate-card" elevation="0">
          <div class="metric-gradient gradient-green"></div>
          <v-card-text class="metric-content">
            <div class="metric-icon-wrapper green-gradient">
              <v-icon size="32" color="white">mdi-check-circle-outline</v-icon>
            </div>
            <div class="metric-info">
              <div class="metric-value">{{ calculateResolutionRate() }}%</div>
              <div class="metric-label">Resolution Rate</div>
              <div class="metric-change positive">
                <v-icon size="16">mdi-trending-up</v-icon>
                <span>Good performance</span>
              </div>
            </div>
          </v-card-text>
          <div class="metric-footer">
            <v-icon size="14" class="me-1">mdi-information-outline</v-icon>
            <span>Tickets resolved successfully</span>
          </div>
        </v-card>

        <!-- Avg Resolution Time Card -->
        <v-card class="metric-card avg-resolution-card" elevation="0">
          <div class="metric-gradient gradient-orange"></div>
          <v-card-text class="metric-content">
            <div class="metric-icon-wrapper orange-gradient">
              <v-icon size="32" color="white">mdi-clock-fast</v-icon>
            </div>
            <div class="metric-info">
              <div class="metric-value">{{ formatHours(statistics?.avg_resolution_time_hours || null) }}</div>
              <div class="metric-label">Avg Resolution Time</div>
              <div class="metric-change" :class="getResolutionTimeClass()">
                <v-icon size="16">mdi-clock-outline</v-icon>
                <span>{{ getResolutionTimeStatus() }}</span>
              </div>
            </div>
          </v-card-text>
          <div class="metric-footer">
            <v-icon size="14" class="me-1">mdi-information-outline</v-icon>
            <span>Average time to resolve</span>
          </div>
        </v-card>

        <!-- Critical Tickets Card -->
        <v-card class="metric-card critical-tickets-card" elevation="0">
          <div class="metric-gradient gradient-red"></div>
          <v-card-text class="metric-content">
            <div class="metric-icon-wrapper red-gradient">
              <v-icon size="32" color="white">mdi-alert-circle-outline</v-icon>
            </div>
            <div class="metric-info">
              <div class="metric-value">{{ (statistics?.high_priority_tickets || 0) + (statistics?.critical_priority_tickets || 0) }}</div>
              <div class="metric-label">High Priority Tickets</div>
              <div class="metric-change warning">
                <v-icon size="16">mdi-alert</v-icon>
                <span>Needs attention</span>
              </div>
            </div>
          </v-card-text>
          <div class="metric-footer">
            <v-icon size="14" class="me-1">mdi-information-outline</v-icon>
            <span>High & Critical priority</span>
          </div>
        </v-card>
      </div>
    </div>

    <!-- ===== ENHANCED CHARTS SECTION ===== -->
    <div class="charts-section">
      <v-row>
        <!-- Monthly Trends Chart -->
        <v-col cols="12" lg="8">
          <v-card class="chart-card" elevation="0">
            <v-card-title class="chart-header">
              <div class="chart-title-wrapper">
                <v-icon class="me-3" color="primary">mdi-chart-line</v-icon>
                <div>
                  <h3 class="chart-title">Monthly Trends</h3>
                  <p class="chart-subtitle">Ticket volume and resolution trends</p>
                </div>
              </div>
              <v-btn-toggle
                v-model="trendPeriod"
                mandatory
                variant="outlined"
                density="compact"
                class="period-toggle"
              >
                <v-btn value="6" size="small">6M</v-btn>
                <v-btn value="12" size="small">1Y</v-btn>
                <v-btn value="24" size="small">2Y</v-btn>
              </v-btn-toggle>
            </v-card-title>
            <v-divider></v-divider>
            <v-card-text class="pa-6">
              <div v-if="loadingMonthly" class="loading-state">
                <v-progress-circular 
                  indeterminate 
                  color="primary" 
                  size="64"
                  width="6"
                ></v-progress-circular>
                <p class="loading-text">Loading monthly trends...</p>
              </div>
              <div v-else-if="monthlyTrends.length > 0" class="trends-chart">
                <Line
                  :data="trendsChartData"
                  :options="trendsChartOptions"
                  height="120"
                />
              </div>
              <div v-else class="empty-state">
                <div class="empty-state-icon">
                  <v-icon size="64" color="primary-lighten-1">mdi-chart-line</v-icon>
                </div>
                <p class="empty-state-title">No Trend Data Available</p>
                <p class="empty-state-text">Data will appear here once tickets are created</p>
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- Category Distribution -->
        <v-col cols="12" lg="4">
          <v-card class="chart-card" elevation="0">
            <v-card-title class="chart-header">
              <div class="chart-title-wrapper">
                <v-icon class="me-3" color="primary">mdi-chart-pie</v-icon>
                <div>
                  <h3 class="chart-title">Category Distribution</h3>
                  <p class="chart-subtitle">Tickets by category</p>
                </div>
              </div>
            </v-card-title>
            <v-divider></v-divider>
            <v-card-text class="pa-6">
              <div v-if="loadingCategory" class="loading-state">
                <v-progress-circular 
                  indeterminate 
                  color="primary" 
                  size="64"
                  width="6"
                ></v-progress-circular>
                <p class="loading-text">Loading category data...</p>
              </div>
              <div v-else-if="categoryPerformance.length > 0" class="category-chart">
                <Pie
                  :data="categoryChartData"
                  :options="categoryChartOptions"
                  height="200"
                />
              </div>
              <div v-else class="empty-state">
                <div class="empty-state-icon">
                  <v-icon size="64" color="primary-lighten-1">mdi-chart-pie</v-icon>
                </div>
                <p class="empty-state-title">No Category Data</p>
                <p class="empty-state-text">Data will appear once categorized</p>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </div>

    <!-- ===== ENHANCED DETAILED TABLES SECTION ===== -->
    <div class="tables-section">
      <v-row>
        <!-- Category Performance Table -->
        <v-col cols="12" lg="6">
          <v-card class="table-card" elevation="0">
            <v-card-title class="table-header">
              <div class="table-title-wrapper">
                <v-icon class="me-3" color="primary">mdi-tag-outline</v-icon>
                <div>
                  <h3 class="table-title">Category Performance</h3>
                  <p class="table-subtitle">Performance metrics by category</p>
                </div>
              </div>
              <v-chip size="small" color="info" variant="flat" prepend-icon="mdi-tag-multiple">
                {{ categoryPerformance.length }} Categories
              </v-chip>
            </v-card-title>
            <v-divider></v-divider>
            <v-card-text class="pa-0">
              <div v-if="loadingCategory" class="loading-state">
                <v-progress-circular 
                  indeterminate 
                  color="primary" 
                  size="48"
                  width="5"
                ></v-progress-circular>
                <p class="loading-text">Loading category performance...</p>
              </div>
              <v-data-table
                v-else
                :headers="categoryHeaders"
                :items="categoryPerformance"
                :loading="loadingCategory"
                class="enhanced-table category-table"
                density="comfortable"
                hide-default-footer
                :items-per-page="-1"
              >
                <template v-slot:item.category="{ item }">
                  <v-chip
                    size="small"
                    variant="flat"
                    color="info"
                    prepend-icon="mdi-tag-outline"
                    class="category-chip"
                  >
                    {{ item.category_display }}
                  </v-chip>
                </template>
                <template v-slot:item.resolution_rate="{ item }">
                  <div class="progress-wrapper">
                    <v-progress-linear
                      :model-value="item.resolution_rate_percent"
                      :color="getResolutionRateColor(item.resolution_rate_percent)"
                      height="24"
                      rounded
                      class="resolution-progress"
                    >
                      <template v-slot:default="{ value }">
                        <strong class="progress-text">
                          {{ Math.ceil(value) }}%
                        </strong>
                      </template>
                    </v-progress-linear>
                  </div>
                </template>
                <template v-slot:item.avg_resolution="{ item }">
                  <v-chip size="small" variant="tonal" color="primary">
                    {{ formatHours(item.avg_resolution_hours) }}
                  </v-chip>
                </template>
              </v-data-table>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- User Performance Table -->
        <v-col cols="12" lg="6">
          <v-card class="table-card" elevation="0">
            <v-card-title class="table-header">
              <div class="table-title-wrapper">
                <v-icon class="me-3" color="primary">mdi-account-group-outline</v-icon>
                <div>
                  <h3 class="table-title">Technician Performance</h3>
                  <p class="table-subtitle">Individual technician metrics</p>
                </div>
              </div>
              <v-chip size="small" color="success" variant="flat" prepend-icon="mdi-account-multiple">
                {{ userPerformance.length }} Technicians
              </v-chip>
            </v-card-title>
            <v-divider></v-divider>
            <v-card-text class="pa-0">
              <div v-if="loadingUser" class="loading-state">
                <v-progress-circular 
                  indeterminate 
                  color="primary" 
                  size="48"
                  width="5"
                ></v-progress-circular>
                <p class="loading-text">Loading user performance...</p>
              </div>
              <v-data-table
                v-else
                :headers="userHeaders"
                :items="userPerformance"
                :loading="loadingUser"
                class="enhanced-table user-table"
                density="comfortable"
                hide-default-footer
                :items-per-page="-1"
              >
                <template v-slot:item.user_name="{ item }">
                  <div class="user-info">
                    <v-avatar size="36" color="success" variant="flat" class="user-avatar">
                      <span class="user-initial">
                        {{ item.user_name.charAt(0).toUpperCase() }}
                      </span>
                    </v-avatar>
                    <span class="user-name">{{ item.user_name }}</span>
                  </div>
                </template>
                <template v-slot:item.resolution_rate="{ item }">
                  <div class="progress-wrapper">
                    <v-progress-linear
                      :model-value="item.resolution_rate_percent"
                      :color="getResolutionRateColor(item.resolution_rate_percent)"
                      height="24"
                      rounded
                      class="resolution-progress"
                    >
                      <template v-slot:default="{ value }">
                        <strong class="progress-text">
                          {{ Math.ceil(value) }}%
                        </strong>
                      </template>
                    </v-progress-linear>
                  </div>
                </template>
                <template v-slot:item.avg_resolution="{ item }">
                  <v-chip size="small" variant="tonal" color="primary">
                    {{ formatHours(item.avg_resolution_hours) }}
                  </v-chip>
                </template>
              </v-data-table>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </div>

    <!-- ===== ENHANCED DOWNTIME ANALYSIS SECTION ===== -->
    <div class="downtime-section">
      <v-card class="downtime-card" elevation="0">
        <v-card-title class="downtime-header">
          <div class="downtime-title-wrapper">
            <v-icon class="me-3" color="primary">mdi-clock-alert-outline</v-icon>
            <div>
              <h3 class="downtime-title">Downtime Analysis</h3>
              <p class="downtime-subtitle">Track and analyze service interruptions</p>
            </div>
          </div>
          <v-btn
            variant="outlined"
            prepend-icon="mdi-refresh"
            @click="loadDowntimeAnalysis"
            :loading="loadingDowntime"
            size="small"
            color="primary"
          >
            Refresh
          </v-btn>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-6">
          <div v-if="loadingDowntime" class="loading-state">
            <v-progress-circular 
              indeterminate 
              color="primary" 
              size="64"
              width="6"
            ></v-progress-circular>
            <p class="loading-text">Analyzing downtime data...</p>
          </div>
          <div v-else-if="downtimeAnalysis" class="downtime-content">
            <!-- Overall Statistics -->
            <div class="downtime-overview">
              <h4 class="subsection-title">
                <v-icon size="20" class="me-2">mdi-chart-box</v-icon>
                Overall Downtime Statistics
              </h4>
              <div class="downtime-metrics-grid">
                <div class="downtime-metric-card">
                  <div class="downtime-metric-icon blue-bg">
                    <v-icon color="white">mdi-clock-outline</v-icon>
                  </div>
                  <div class="downtime-metric-info">
                    <div class="downtime-metric-value">{{ formatHours(downtimeAnalysis.overall_statistics.total_downtime_hours) }}</div>
                    <div class="downtime-metric-label">Total Downtime</div>
                  </div>
                </div>
                <div class="downtime-metric-card">
                  <div class="downtime-metric-icon green-bg">
                    <v-icon color="white">mdi-chart-timeline-variant</v-icon>
                  </div>
                  <div class="downtime-metric-info">
                    <div class="downtime-metric-value">{{ formatHours(downtimeAnalysis.overall_statistics.avg_downtime_hours) }}</div>
                    <div class="downtime-metric-label">Average Downtime</div>
                  </div>
                </div>
                <div class="downtime-metric-card">
                  <div class="downtime-metric-icon orange-bg">
                    <v-icon color="white">mdi-clock-alert</v-icon>
                  </div>
                  <div class="downtime-metric-info">
                    <div class="downtime-metric-value">{{ formatHours(downtimeAnalysis.overall_statistics.max_downtime_hours) }}</div>
                    <div class="downtime-metric-label">Maximum Downtime</div>
                  </div>
                </div>
                <div class="downtime-metric-card">
                  <div class="downtime-metric-icon red-bg">
                    <v-icon color="white">mdi-ticket-alert</v-icon>
                  </div>
                  <div class="downtime-metric-info">
                    <div class="downtime-metric-value">{{ downtimeAnalysis.overall_statistics.tickets_with_downtime }}</div>
                    <div class="downtime-metric-label">Affected Tickets</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Top Customers with Downtime -->
            <div class="top-customers" v-if="downtimeAnalysis.top_customers.length > 0">
              <h4 class="subsection-title">
                <v-icon size="20" class="me-2">mdi-account-alert</v-icon>
                Top Customers by Downtime
              </h4>
              <v-data-table
                :headers="customerDowntimeHeaders"
                :items="downtimeAnalysis.top_customers.slice(0, 5)"
                density="comfortable"
                hide-default-footer
                class="enhanced-table customer-downtime-table"
              >
                <template v-slot:item.customer_name="{ item }">
                  <div class="customer-info">
                    <v-avatar size="36" color="warning" variant="flat" class="customer-avatar">
                      <span class="customer-initial">
                        {{ item.customer_name.charAt(0).toUpperCase() }}
                      </span>
                    </v-avatar>
                    <span class="customer-name">{{ item.customer_name }}</span>
                  </div>
                </template>
                <template v-slot:item.total_downtime="{ item }">
                  <v-chip
                    size="small"
                    :color="getDowntimeSeverityColor(item.total_downtime_hours)"
                    variant="flat"
                    class="downtime-chip"
                  >
                    <v-icon size="14" class="me-1">mdi-clock-alert</v-icon>
                    {{ formatHours(item.total_downtime_hours) }}
                  </v-chip>
                </template>
                <template v-slot:item.avg_downtime_hours="{ item }">
                  <v-chip size="small" variant="tonal" color="warning">
                    {{ formatHours(item.avg_downtime_hours) }}
                  </v-chip>
                </template>
              </v-data-table>
            </div>
          </div>
          <div v-else class="empty-state">
            <div class="empty-state-icon">
              <v-icon size="64" color="warning-lighten-1">mdi-clock-alert-outline</v-icon>
            </div>
            <p class="empty-state-title">No Downtime Data Available</p>
            <p class="empty-state-text">Downtime information will appear here when available</p>
          </div>
        </v-card-text>
      </v-card>
    </div>

    <!-- ===== ENHANCED TICKET DETAILS SECTION ===== -->
    <div class="ticket-details-section">
      <v-card class="ticket-details-card" elevation="0">
        <v-card-title class="ticket-details-header">
          <div class="ticket-details-title-wrapper">
            <v-icon class="me-3" color="primary">mdi-ticket-account</v-icon>
            <div>
              <h3 class="ticket-details-title">Ticket Details with Customer Information</h3>
              <p class="ticket-details-subtitle">Complete ticket information and history</p>
            </div>
          </div>
          <div class="ticket-details-actions">
            <v-chip size="small" color="info" variant="flat" prepend-icon="mdi-ticket">
              {{ ticketDetails.length }} Total Tickets
            </v-chip>
            <v-btn
              variant="outlined"
              prepend-icon="mdi-refresh"
              @click="loadTicketDetails"
              :loading="loadingTicketDetails"
              size="small"
              color="primary"
              class="ms-2"
            >
              Refresh
            </v-btn>
          </div>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-6">
          <div v-if="loadingTicketDetails" class="loading-state">
            <v-progress-circular 
              indeterminate 
              color="primary" 
              size="64"
              width="6"
            ></v-progress-circular>
            <p class="loading-text">Loading ticket details...</p>
          </div>
          <div v-else-if="ticketDetails.length > 0" class="ticket-details-content">
            <!-- Enhanced Filters -->
            <div class="ticket-filters-card">
              <v-row>
                <v-col cols="12" md="4">
                  <v-text-field
                    v-model="ticketSearch"
                    label="Search tickets..."
                    prepend-inner-icon="mdi-magnify"
                    variant="outlined"
                    density="comfortable"
                    hide-details
                    clearable
                    class="search-field"
                  ></v-text-field>
                </v-col>
                <v-col cols="12" md="3">
                  <v-select
                    v-model="ticketStatusFilter"
                    :items="ticketStatusOptions"
                    label="Filter by Status"
                    prepend-inner-icon="mdi-filter"
                    variant="outlined"
                    density="comfortable"
                    hide-details
                    clearable
                    class="filter-select"
                  ></v-select>
                </v-col>
                <v-col cols="12" md="3">
                  <v-select
                    v-model="ticketPriorityFilter"
                    :items="ticketPriorityOptions"
                    label="Filter by Priority"
                    prepend-inner-icon="mdi-flag"
                    variant="outlined"
                    density="comfortable"
                    hide-details
                    clearable
                    class="filter-select"
                  ></v-select>
                </v-col>
                <v-col cols="12" md="2">
                  <v-btn
                    variant="outlined"
                    prepend-icon="mdi-filter-remove"
                    @click="clearTicketFilters"
                    size="large"
                    block
                    color="error"
                  >
                    Clear
                  </v-btn>
                </v-col>
              </v-row>
            </div>

            <!-- Enhanced Ticket Details Table -->
            <v-data-table
              :headers="ticketDetailsHeaders"
              :items="filteredTicketDetails"
              :loading="loadingTicketDetails"
              density="comfortable"
              :items-per-page="ticketDetailsPerPage"
              v-model:page="ticketDetailsPage"
              class="enhanced-table ticket-details-table"
            >
              <!-- Ticket Number -->
              <template v-slot:item.ticket_number="{ item }">
                <v-chip
                  color="primary"
                  variant="flat"
                  size="small"
                  prepend-icon="mdi-ticket"
                  class="ticket-number-chip"
                >
                  {{ item.ticket_number }}
                </v-chip>
              </template>

              <!-- Customer Information -->
              <template v-slot:item.customer_info="{ item }">
                <div class="customer-info-cell">
                  <div class="customer-name-row">
                    <v-icon size="16" color="primary" class="me-1">mdi-account</v-icon>
                    <span class="customer-name-text">{{ item.customer_name }}</span>
                  </div>
                  <div class="customer-detail-row">
                    <v-icon size="14" color="primary-lighten-1" class="me-1">mdi-phone</v-icon>
                    <span class="customer-detail-text">{{ item.customer_phone }}</span>
                  </div>
                  <div class="customer-detail-row">
                    <v-icon size="14" color="primary-lighten-1" class="me-1">mdi-map-marker</v-icon>
                    <span class="customer-detail-text">{{ item.customer_address.substring(0, 50) }}{{ item.customer_address.length > 50 ? '...' : '' }}</span>
                  </div>
                </div>
              </template>

              <!-- Technical Details -->
              <template v-slot:item.technical_info="{ item }">
                <div class="technical-info-cell">
                  <div class="tech-detail-row">
                    <span class="tech-label">IP:</span>
                    <v-chip size="x-small" variant="tonal" color="info" class="tech-chip">
                      {{ item.ip_pelanggan }}
                    </v-chip>
                  </div>
                  <div class="tech-detail-row">
                    <span class="tech-label">ID:</span>
                    <v-chip size="x-small" variant="tonal" color="info" class="tech-chip">
                      {{ item.id_pelanggan }}
                    </v-chip>
                  </div>
                  <div classs="tech-detail-row">
                    <span class="tech-label">ONU:</span>
                    <v-chip size="x-small" variant="tonal" color="success" class="tech-chip">
                      {{ item.onu_power }} dBm
                    </v-chip>
                  </div>
                </div>
              </template>

              <!-- Problem Description -->
              <template v-slot:item.problem="{ item }">
                <div class="problem-cell">
                  <div class="problem-title-text">{{ item.title }}</div>
                  <div class="problem-description-text">{{ item.description.substring(0, 100) }}{{ item.description.length > 100 ? '...' : '' }}</div>
                  <v-chip size="x-small" variant="tonal" color="info" class="problem-category-chip">
                    {{ formatCategory(item.category) }}
                  </v-chip>
                </div>
              </template>

              <!-- Status & Priority -->
              <template v-slot:item.status_priority="{ item }">
                <div class="status-priority-cell">
                  <v-chip
                    :color="getStatusColor(item.status)"
                    size="small"
                    variant="flat"
                    class="status-chip"
                  >
                    {{ formatStatus(item.status) }}
                  </v-chip>
                  <v-chip
                    :color="getPriorityColor(item.priority)"
                    size="small"
                    variant="flat"
                    class="priority-chip"
                  >
                    {{ formatPriority(item.priority) }}
                  </v-chip>
                </div>
              </template>

              <!-- Downtime -->
              <template v-slot:item.downtime="{ item }">
                <div class="downtime-cell">
                  <v-chip
                    :color="getDowntimeColor(item.total_downtime_minutes)"
                    size="small"
                    variant="flat"
                    class="downtime-chip-main"
                  >
                    <v-icon size="14" class="me-1">mdi-clock-alert</v-icon>
                    {{ item.downtime_hours }}h
                  </v-chip>
                  <div class="downtime-minutes">
                    {{ item.total_downtime_minutes }} minutes
                  </div>
                </div>
              </template>

              <!-- Assignment -->
              <template v-slot:item.assignment="{ item }">
                <div class="assignment-cell">
                  <div class="assigned-user-row">
                    <v-icon size="16" color="success" class="me-1">mdi-account-check</v-icon>
                    <span class="assigned-user-text">{{ item.assigned_to }}</span>
                  </div>
                  <v-chip size="x-small" variant="outlined" color="primary" class="action-count-chip">
                    {{ item.latest_actions.length }} actions
                  </v-chip>
                </div>
              </template>
            </v-data-table>
          </div>
          <div v-else class="empty-state">
            <div class="empty-state-icon">
              <v-icon size="64" color="primary-lighten-1">mdi-ticket-outline</v-icon>
            </div>
            <p class="empty-state-title">No Ticket Details Available</p>
            <p class="empty-state-text">Click the button below to load ticket information</p>
            <v-btn
              variant="outlined"
              prepend-icon="mdi-refresh"
              @click="loadTicketDetails"
              class="mt-4 load-tickets-btn"
              color="primary"
              size="large"
              elevation="2"
            >
              Load Tickets
            </v-btn>
          </div>
        </v-card-text>
      </v-card>
    </div>

    <!-- ===== ENHANCED EXPORT DIALOG ===== -->
    <v-dialog v-model="showExportDialog" max-width="600" persistent class="export-dialog">
      <v-card class="export-dialog-card" elevation="8">
        <v-card-title class="export-dialog-header">
          <div class="export-header-content">
            <div class="export-icon-wrapper">
              <v-icon size="32" color="white">mdi-download</v-icon>
            </div>
            <div>
              <h3 class="export-dialog-title">Export Report</h3>
              <p class="export-dialog-subtitle">Choose your preferred export format</p>
            </div>
          </div>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-6">
          <p class="export-description">Select the format that best suits your needs:</p>

          <v-list class="export-options-list">
            <v-list-item
              v-for="format in exportFormats"
              :key="format.value"
              @click="selectExportFormat(format.value)"
              class="export-option-item"
              :disabled="exporting"
            >
              <template v-slot:prepend>
                <div class="export-format-icon" :class="`${format.color}-bg`">
                  <v-icon :color="'white'" size="28">{{ format.icon }}</v-icon>
                </div>
              </template>
              <v-list-item-title class="export-format-title">
                {{ format.title }}
              </v-list-item-title>
              <v-list-item-subtitle class="export-format-description">
                {{ format.description }}
              </v-list-item-subtitle>
              <template v-slot:append>
                <v-icon color="primary-lighten-1">mdi-chevron-right</v-icon>
              </template>
            </v-list-item>
          </v-list>

          <v-alert
            v-if="exporting"
            type="info"
            variant="tonal"
            class="mt-4 export-progress-alert"
            density="comfortable"
          >
            <div class="export-progress-content">
              <v-progress-circular
                indeterminate
                size="20"
                width="3"
                color="info"
                class="me-3"
              ></v-progress-circular>
              <div>
                <strong>Exporting report...</strong>
                <p class="text-caption mb-0">Please wait while we prepare your file</p>
              </div>
            </div>
          </v-alert>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions class="pa-4 export-dialog-actions">
          <v-spacer></v-spacer>
          <v-btn
            variant="outlined"
            @click="closeExportDialog"
            :disabled="exporting"
            size="large"
            color="primary"
          >
            Cancel
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import apiClient from '@/services/api'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'
import { Line, Pie } from 'vue-chartjs'

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

// Types
interface Statistics {
  total_tickets: number
  open_tickets: number
  in_progress_tickets: number
  resolved_tickets: number
  closed_tickets: number
  high_priority_tickets: number
  critical_priority_tickets: number
  avg_resolution_time_hours: number | null
  tickets_this_month: number
  unresolved_over_24h: number
}

interface ExcelSheet {
  name: string
  data: string[][]
}

interface CategoryPerformance {
  category: string
  category_display: string
  total_tickets: number
  resolved_tickets: number
  resolution_rate_percent: number
  avg_resolution_hours: number
  avg_downtime_minutes: number
  total_downtime_minutes: number
}

interface UserPerformance {
  user_id: number
  user_name: string
  total_assigned: number
  resolved_tickets: number
  resolution_rate_percent: number
  avg_resolution_hours: number
  first_ticket_date: string | null
  last_ticket_date: string | null
}

interface DowntimeAnalysis {
  overall_statistics: {
    total_downtime_minutes: number
    total_downtime_hours: number
    total_downtime_days: number
    avg_downtime_minutes: number
    avg_downtime_hours: number
    max_downtime_minutes: number
    max_downtime_hours: number
    tickets_with_downtime: number
  }
  by_category: Array<{
    category: string
    category_display: string
    total_downtime_minutes: number
    avg_downtime_minutes: number
    ticket_count: number
    total_downtime_hours: number
    avg_downtime_hours: number
  }>
  top_customers: Array<{
    customer_id: number
    customer_name: string
    total_downtime_minutes: number
    ticket_count: number
    avg_downtime_minutes: number
    total_downtime_hours: number
    avg_downtime_hours: number
  }>
}

interface MonthlyTrend {
  month: string
  month_name: string
  statistics: {
    total: number
    resolved: number
    avg_resolution_hours: number
    by_category: Record<string, number>
    by_priority: Record<string, number>
  }
}

// State
const loading = ref(false)
const loadingMonthly = ref(false)
const loadingCategory = ref(false)
const loadingUser = ref(false)
const loadingDowntime = ref(false)
const loadingTicketDetails = ref(false)
const exporting = ref(false)
const showExportDialog = ref(false)

// Ticket details data for display
const ticketDetails = ref<any[]>([])
const ticketDetailsPage = ref(1)
const ticketDetailsPerPage = ref(10)

// Filter states
const ticketSearch = ref('')
const ticketStatusFilter = ref('')
const ticketPriorityFilter = ref('')

// Filter options
const ticketStatusOptions = [
  { title: 'Open', value: 'open' },
  { title: 'In Progress', value: 'in_progress' },
  { title: 'Pending Customer', value: 'pending_customer' },
  { title: 'Pending Vendor', value: 'pending_vendor' },
  { title: 'Resolved', value: 'resolved' },
  { title: 'Closed', value: 'closed' },
  { title: 'Cancelled', value: 'cancelled' }
]

const ticketPriorityOptions = [
  { title: 'Low', value: 'low' },
  { title: 'Medium', value: 'medium' },
  { title: 'High', value: 'high' },
  { title: 'Critical', value: 'critical' }
]

// Computed filtered tickets
const filteredTicketDetails = computed(() => {
  return ticketDetails.value.filter(ticket => {
    const matchesSearch = !ticketSearch.value ||
      ticket.ticket_number.toLowerCase().includes(ticketSearch.value.toLowerCase()) ||
      ticket.customer_name.toLowerCase().includes(ticketSearch.value.toLowerCase()) ||
      ticket.title.toLowerCase().includes(ticketSearch.value.toLowerCase()) ||
      ticket.description.toLowerCase().includes(ticketSearch.value.toLowerCase())

    const matchesStatus = !ticketStatusFilter.value || ticket.status === ticketStatusFilter.value
    const matchesPriority = !ticketPriorityFilter.value || ticket.priority === ticketPriorityFilter.value

    return matchesSearch && matchesStatus && matchesPriority
  })
})

const statistics = ref<Statistics | null>(null)
const monthlyTrends = ref<MonthlyTrend[]>([])
const categoryPerformance = ref<CategoryPerformance[]>([])
const userPerformance = ref<UserPerformance[]>([])
const downtimeAnalysis = ref<DowntimeAnalysis | null>(null)

const trendPeriod = ref('12')
const dateRange = reactive({
  from: '',
  to: ''
})


// Chart data properties
const trendsChartData = ref({
  labels: [] as string[],
  datasets: [
    {
      label: 'Tickets Created',
      data: [] as number[],
      borderColor: 'rgb(59, 130, 246)',
      backgroundColor: 'rgba(59, 130, 246, 0.1)',
      tension: 0.4,
      fill: true
    },
    {
      label: 'Tickets Resolved',
      data: [] as number[],
      borderColor: 'rgb(34, 197, 94)',
      backgroundColor: 'rgba(34, 197, 94, 0.1)',
      tension: 0.4,
      fill: true
    }
  ]
})

const categoryChartData = ref({
  labels: [] as string[],
  datasets: [
    {
      label: 'Tickets by Category',
      data: [] as number[],
      backgroundColor: [
        '#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6',
        '#EC4899', '#14B8A6', '#F97316', '#06B6D4', '#84CC16'
      ],
      borderWidth: 2,
      borderColor: '#ffffff'
    }
  ]
})

// Chart options
const trendsChartOptions = ref({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top' as const,
      labels: {
        usePointStyle: true,
        padding: 20
      }
    },
    tooltip: {
      mode: 'index' as const,
      intersect: false,
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      titleColor: '#ffffff',
      bodyColor: '#ffffff',
      borderColor: 'rgba(255, 255, 255, 0.1)',
      borderWidth: 1
    }
  },
  scales: {
    x: {
      display: true,
      grid: {
        display: false
      }
    },
    y: {
      display: true,
      beginAtZero: true,
      ticks: {
        stepSize: 1
      }
    }
  }
})

const categoryChartOptions = ref({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'right' as const,
      labels: {
        usePointStyle: true,
        padding: 15,
        generateLabels: function(chart: any) {
          const data = chart.data
          if (data.labels.length && data.datasets.length) {
            const dataset = data.datasets[0]
            const total = dataset.data.reduce((a: number, b: number) => a + b, 0)
            return data.labels.map((label: string, i: number) => {
              const value = dataset.data[i]
              const percentage = ((value / total) * 100).toFixed(1)
              return {
                text: `${label} (${percentage}%)`,
                fillStyle: dataset.backgroundColor[i],
                hidden: false,
                index: i
              }
            })
          }
          return []
        }
      }
    },
    tooltip: {
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      titleColor: '#ffffff',
      bodyColor: '#ffffff',
      borderColor: 'rgba(255, 255, 255, 0.1)',
      borderWidth: 1,
      callbacks: {
        label: function(context: any) {
          const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0)
          const percentage = ((context.parsed / total) * 100).toFixed(1)
          return `${context.label}: ${context.parsed} (${percentage}%)`
        }
      }
    }
  }
})

// Table headers
const categoryHeaders = [
  { title: 'Category', key: 'category', sortable: false },
  { title: 'Total', key: 'total_tickets', sortable: false },
  { title: 'Resolved', key: 'resolved_tickets', sortable: false },
  { title: 'Resolution Rate', key: 'resolution_rate', sortable: false },
  { title: 'Avg Resolution', key: 'avg_resolution', sortable: false }
]

const userHeaders = [
  { title: 'Technician', key: 'user_name', sortable: false },
  { title: 'Assigned', key: 'total_assigned', sortable: false },
  { title: 'Resolved', key: 'resolved_tickets', sortable: false },
  { title: 'Resolution Rate', key: 'resolution_rate', sortable: false },
  { title: 'Avg Resolution', key: 'avg_resolution', sortable: false }
]

const customerDowntimeHeaders = [
  { title: 'Customer', key: 'customer_name', sortable: false },
  { title: 'Tickets', key: 'ticket_count', sortable: false },
  { title: 'Total Downtime', key: 'total_downtime', sortable: false },
  { title: 'Avg Downtime', key: 'avg_downtime_hours', sortable: false }
]

// Ticket Details Table Headers
const ticketDetailsHeaders = [
  { title: 'Ticket #', key: 'ticket_number', sortable: false, width: '120px' },
  { title: 'Customer Information', key: 'customer_info', sortable: false, width: '200px' },
  { title: 'Technical Details', key: 'technical_info', sortable: false, width: '150px' },
  { title: 'Problem', key: 'problem', sortable: false, width: '250px' },
  { title: 'Status & Priority', key: 'status_priority', sortable: false, width: '140px' },
  { title: 'Downtime', key: 'downtime', sortable: false, width: '100px' },
  { title: 'Assignment', key: 'assignment', sortable: false, width: '150px' }
]

// Helper methods
const calculateResolutionRate = () => {
  if (!statistics.value) return 0
  const total = statistics.value.total_tickets
  const resolved = statistics.value.resolved_tickets + statistics.value.closed_tickets
  return total > 0 ? Math.round((resolved / total) * 100) : 0
}

const getResolutionTimeClass = () => {
  const hours = statistics.value?.avg_resolution_time_hours || 0
  if (hours < 24) return 'positive'
  if (hours < 72) return 'warning'
  return 'negative'
}

const getResolutionTimeStatus = () => {
  const hours = statistics.value?.avg_resolution_time_hours || 0
  if (hours < 24) return 'Excellent'
  if (hours < 72) return 'Good'
  return 'Needs Improvement'
}

const formatHours = (hours: number | null) => {
  if (!hours) return '0h'
  if (hours < 1) return `${Math.round(hours * 60)}m`
  if (hours < 24) return `${Math.round(hours)}h`
  return `${Math.round(hours / 24)}d ${Math.round(hours % 24)}h`
}

const getResolutionRateColor = (rate: number) => {
  if (rate >= 90) return 'success'
  if (rate >= 70) return 'warning'
  return 'error'
}

const getDowntimeSeverityColor = (hours: number) => {
  if (hours < 1) return 'success'
  if (hours < 6) return 'warning'
  return 'error'
}

const formatDate = (dateString: string | null | undefined) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleDateString('id-ID')
}

const showNotification = (message: string, type: 'success' | 'error' | 'info' | 'warning' = 'info') => {
  const colors = {
    success: '#4caf50',
    error: '#f44336',
    info: '#2196f3',
    warning: '#ff9800'
  }

  const notification = document.createElement('div')
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: ${colors[type]};
    color: white;
    padding: 16px 24px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    z-index: 9999;
    font-family: Arial, sans-serif;
    font-size: 14px;
    max-width: 300px;
    animation: slideIn 0.3s ease;
  `
  notification.textContent = message

  document.body.appendChild(notification)

  setTimeout(() => {
    if (notification.parentNode) {
      notification.style.animation = 'slideOut 0.3s ease'
      setTimeout(() => {
        notification.parentNode?.removeChild(notification)
      }, 300)
    }
  }, 5000)
}

// Chart rendering is now handled by vue-chartjs components

// Methods
const loadStatistics = async () => {
  try {
    const response = await apiClient.get('/trouble-tickets/statistics/dashboard')
    statistics.value = response.data
  } catch (error) {
    console.error('Failed to load statistics:', error)
  }
}

const loadMonthlyTrends = async () => {
  loadingMonthly.value = true
  try {
    const params: any = { months: parseInt(trendPeriod.value) }
    if (dateRange.from) params.date_from = dateRange.from
    if (dateRange.to) params.date_to = dateRange.to

    const response = await apiClient.get('/trouble-tickets/reports/monthly-trends', { params })
    monthlyTrends.value = response.data.trends || []

    // Update chart data
    if (monthlyTrends.value.length > 0) {
      const sortedTrends = [...monthlyTrends.value].sort((a, b) =>
        new Date(a.month).getTime() - new Date(b.month).getTime()
      )

      trendsChartData.value.labels = sortedTrends.map(item => {
        const date = new Date(item.month)
        return date.toLocaleDateString('id-ID', { month: 'short', year: 'numeric' })
      })
      trendsChartData.value.datasets[0].data = sortedTrends.map(item => item.statistics.total)
      trendsChartData.value.datasets[1].data = sortedTrends.map(item => item.statistics.resolved)
    }
  } catch (error) {
    console.error('Failed to load monthly trends:', error)
    monthlyTrends.value = []
  } finally {
    loadingMonthly.value = false
  }
}

const loadCategoryPerformance = async () => {
  loadingCategory.value = true
  try {
    const params: any = {}
    if (dateRange.from) params.date_from = dateRange.from
    if (dateRange.to) params.date_to = dateRange.to

    const response = await apiClient.get('/trouble-tickets/reports/category-performance', { params })
    categoryPerformance.value = response.data.category_performance || []

    // Update chart data
    if (categoryPerformance.value.length > 0) {
      categoryChartData.value.labels = categoryPerformance.value.map(item => item.category)
      categoryChartData.value.datasets[0].data = categoryPerformance.value.map(item => item.total_tickets)
    }
  } catch (error: any) {
    console.error('Failed to load category performance:', error)
    showNotification('Failed to load category performance data. Please try again later.', 'error')
    categoryPerformance.value = []
  } finally {
    loadingCategory.value = false
  }
}

const loadUserPerformance = async () => {
  loadingUser.value = true
  try {
    const params: any = {}
    if (dateRange.from) params.date_from = dateRange.from
    if (dateRange.to) params.date_to = dateRange.to

    const response = await apiClient.get('/trouble-tickets/reports/user-performance', { params })
    userPerformance.value = response.data.user_performance || []
  } catch (error: any) {
    console.error('Failed to load user performance:', error)
    showNotification('Failed to load user performance data. Please try again later.', 'error')
    userPerformance.value = []
  } finally {
    loadingUser.value = false
  }
}

const loadDowntimeAnalysis = async () => {
  loadingDowntime.value = true
  try {
    const params: any = {}
    if (dateRange.from) params.date_from = dateRange.from
    if (dateRange.to) params.date_to = dateRange.to

    const response = await apiClient.get('/trouble-tickets/reports/downtime-analysis', { params })
    downtimeAnalysis.value = response.data
  } catch (error: any) {
    console.error('Failed to load downtime analysis:', error)
    showNotification('Failed to load downtime analysis data. Please try again later.', 'error')
    downtimeAnalysis.value = null
  } finally {
    loadingDowntime.value = false
  }
}

const refreshAllData = async () => {
  loading.value = true
  try {
    await Promise.all([
      loadStatistics(),
      loadMonthlyTrends(),
      loadCategoryPerformance(),
      loadUserPerformance(),
      loadDowntimeAnalysis(),
      loadTicketDetails()
    ])
  } finally {
    loading.value = false
  }
}

const loadTicketDetails = async () => {
  loadingTicketDetails.value = true
  try {
    const params: any = {
      skip: (ticketDetailsPage.value - 1) * ticketDetailsPerPage.value,
      limit: ticketDetailsPerPage.value,
      include_relations: true,
      ...(dateRange.from && { date_from: dateRange.from }),
      ...(dateRange.to && { date_to: dateRange.to })
    }

    const response = await apiClient.get('/trouble-tickets', { params })
    const tickets = response.data.data

    const detailedTickets = await Promise.all(
      tickets.map(async (ticket: any) => {
        try {
          const actionsResponse = await apiClient.get(`/trouble-tickets/${ticket.id}/actions`)
          const actions = actionsResponse.data

          return {
            ticket_number: ticket.ticket_number,
            title: ticket.title,
            description: ticket.description,
            status: ticket.status,
            priority: ticket.priority,
            category: ticket.category,
            customer_name: ticket.pelanggan?.nama || 'N/A',
            customer_address: ticket.pelanggan?.alamat || 'N/A',
            customer_phone: ticket.pelanggan?.no_telp || 'N/A',
            customer_email: ticket.pelanggan?.email || 'N/A',
            id_pelanggan: ticket.data_teknis?.id_pelanggan || 'N/A',
            ip_pelanggan: ticket.data_teknis?.ip_pelanggan || 'N/A',
            customer_brand: ticket.pelanggan?.harga_layanan?.brand || 'N/A',
            onu_power: ticket.data_teknis?.onu_power || 'N/A',
            onu_sn: ticket.data_teknis?.onu_sn || 'N/A',
            distance_olt: ticket.data_teknis?.distance_olt || 'N/A',
            created_at: ticket.created_at,
            resolved_at: ticket.resolved_at,
            total_downtime_minutes: ticket.total_downtime_minutes,
            downtime_hours: ticket.total_downtime_minutes ? (ticket.total_downtime_minutes / 60).toFixed(2) : '0',
            assigned_to: ticket.assigned_user?.name || 'Unassigned',
            resolution_notes: ticket.resolution_notes || '',
            latest_actions: actions.slice(0, 3).map((action: any) => ({
              action_description: action.action_description || '',
              summary_problem: action.summary_problem || '',
              summary_action: action.summary_action || '',
              action_date: action.created_at,
              taken_by: action.taken_user?.name || 'System'
            })),
            id: ticket.id
          }
        } catch (error) {
          console.error(`Failed to fetch details for ticket ${ticket.id}:`, error)
          return {
            ticket_number: ticket.ticket_number,
            title: ticket.title,
            description: ticket.description,
            status: ticket.status,
            priority: ticket.priority,
            category: ticket.category,
            customer_name: 'Error loading details',
            error: 'Failed to load ticket details',
            id: ticket.id
          }
        }
      })
    )

    ticketDetails.value = detailedTickets
  } catch (error) {
    console.error('Failed to load ticket details:', error)
    showNotification('Failed to load ticket details', 'error')
  } finally {
    loadingTicketDetails.value = false
  }
}

const clearTicketFilters = () => {
  ticketSearch.value = ''
  ticketStatusFilter.value = ''
  ticketPriorityFilter.value = ''
}

const formatStatus = (status: string) => {
  return status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())
}

const formatPriority = (priority: string) => {
  return priority.charAt(0).toUpperCase() + priority.slice(1)
}

const formatCategory = (category: string) => {
  return category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())
}

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    'open': 'info',
    'in_progress': 'warning',
    'pending_customer': 'orange',
    'pending_vendor': 'amber',
    'resolved': 'success',
    'closed': 'blue-grey',
    'cancelled': 'error'
  }
  return colors[status] || 'blue-grey'
}

const getPriorityColor = (priority: string) => {
  const colors: Record<string, string> = {
    'low': 'success',
    'medium': 'warning',
    'high': 'error',
    'critical': 'deep-purple'
  }
  return colors[priority] || 'blue-grey'
}

const getDowntimeColor = (minutes: number | null | undefined) => {
  if (!minutes || minutes <= 0) return 'success'
  if (minutes <= 60) return 'warning'
  if (minutes <= 360) return 'error'
  return 'deep-purple'
}

const applyDateFilter = () => {
  refreshAllData()
}

const clearDateFilter = () => {
  dateRange.from = ''
  dateRange.to = ''
  refreshAllData()
}

// Export formats configuration
const exportFormats = ref([
  {
    value: 'excel',
    title: 'Excel (XLS)',
    description: 'Multi-sheet workbook with proper Excel formatting & complete ticket data',
    icon: 'mdi-file-excel',
    color: 'success'
  },
  {
    value: 'csv',
    title: 'CSV',
    description: 'Complete ticket details with customer info, actions, and history',
    icon: 'mdi-file-delimited',
    color: 'info'
  },
  {
    value: 'pdf',
    title: 'PDF Report',
    description: 'Summary report with key ticket details (20 latest tickets)',
    icon: 'mdi-file-pdf',
    color: 'error'
  },
  {
    value: 'json',
    title: 'JSON Data',
    description: 'Complete raw data including all ticket details and history',
    icon: 'mdi-code-json',
    color: 'warning'
  }
])

const exportReport = () => {
  showExportDialog.value = true
}

const selectExportFormat = async (format: string) => {
  exporting.value = true

  try {
    if (format === 'excel' || format === 'csv') {
      showNotification('Fetching detailed ticket data... This may take a moment.', 'info')
    }

    let ticketDetailsData: any[] = []
    try {
      ticketDetailsData = await fetchTicketDetailsForExport()
    } catch (error) {
      console.error('Failed to fetch ticket details for export:', error)
      showNotification('Warning: Using basic data. Detailed ticket data not available.', 'warning')
    }

    const reportData = {
      metadata: {
        title: 'Trouble Ticket Analysis Report',
        generated_at: new Date().toISOString(),
        period: {
          from: dateRange.from || 'All time',
          to: dateRange.to || 'Present'
        },
        summary: {
          total_tickets: statistics.value?.total_tickets || 0,
          resolution_rate: calculateResolutionRate(),
          avg_resolution_time: formatHours(statistics.value?.avg_resolution_time_hours || null)
        }
      },
      statistics: statistics.value,
      monthly_trends: monthlyTrends.value,
      category_performance: categoryPerformance.value,
      user_performance: userPerformance.value,
      downtime_analysis: downtimeAnalysis.value,
      ticket_details: ticketDetailsData
    }

    switch (format) {
      case 'excel':
        await exportToExcel(reportData)
        break
      case 'csv':
        await exportToCSV(reportData)
        break
      case 'pdf':
        await exportToPDF(reportData)
        break
      case 'json':
        await exportToJSON(reportData)
        break
    }

    closeExportDialog()

  } catch (error) {
    console.error('Export failed:', error)
    showNotification('Export failed. Please try again.', 'error')
  } finally {
    exporting.value = false
  }
}

const closeExportDialog = () => {
  showExportDialog.value = false
}

const fetchTicketDetailsForExport = async () => {
  const detailedTickets: any[] = []

  try {
    const params: any = {
      skip: 0,
      limit: 100,
      include_relations: true,
      ...(dateRange.from && { date_from: dateRange.from }),
      ...(dateRange.to && { date_to: dateRange.to })
    }

    const response = await apiClient.get('/trouble-tickets', { params })
    const tickets = response.data.data

    const batchSize = 10

    for (let i = 0; i < tickets.length; i += batchSize) {
      const batch = tickets.slice(i, i + batchSize)

      const batchResults = await Promise.allSettled(
        batch.map(async (ticket: any) => {
          try {
            const actionsResponse = await apiClient.get(`/trouble-tickets/${ticket.id}/actions`)
            const actions = actionsResponse.data

            const historyResponse = await apiClient.get(`/trouble-tickets/${ticket.id}/history`)
            const history = historyResponse.data

            return {
              ticket_number: ticket.ticket_number,
              title: ticket.title,
              description: ticket.description,
              status: ticket.status,
              priority: ticket.priority,
              category: ticket.category,
              customer_id: ticket.pelanggan?.id || '',
              customer_name: ticket.pelanggan?.nama || 'N/A',
              customer_address: ticket.pelanggan?.alamat || 'N/A',
              customer_phone: ticket.pelanggan?.no_telp || 'N/A',
              customer_email: ticket.pelanggan?.email || 'N/A',
              id_pelanggan: ticket.data_teknis?.id_pelanggan || 'N/A',
              ip_pelanggan: ticket.data_teknis?.ip_pelanggan || 'N/A',
              customer_brand: ticket.pelanggan?.harga_layanan?.brand || 'N/A',
              onu_power: ticket.data_teknis?.onu_power || 'N/A',
              onu_sn: ticket.data_teknis?.onu_sn || 'N/A',
              distance_olt: ticket.data_teknis?.distance_olt || 'N/A',
              created_at: ticket.created_at,
              updated_at: ticket.updated_at,
              resolved_at: ticket.resolved_at,
              downtime_start: ticket.downtime_start,
              downtime_end: ticket.downtime_end,
              total_downtime_minutes: ticket.total_downtime_minutes,
              downtime_hours: ticket.total_downtime_minutes ? (ticket.total_downtime_minutes / 60).toFixed(2) : '0',
              assigned_to: ticket.assigned_user?.name || 'Unassigned',
              assigned_user_id: ticket.assigned_to || '',
              resolution_notes: ticket.resolution_notes || '',
              latest_actions: actions.slice(0, 3).map((action: any) => ({
                action_description: action.action_description || '',
                summary_problem: action.summary_problem || '',
                summary_action: action.summary_action || '',
                action_date: action.created_at,
                taken_by: action.taken_user?.name || 'System'
              })),
              status_history: history.slice(0, 5).map((h: any) => ({
                old_status: h.old_status || 'Created',
                new_status: h.new_status,
                changed_date: h.created_at,
                changed_by: h.changed_user?.name || 'System',
                notes: h.notes || ''
              })),
              evidence: ticket.evidence || '',
              customer_notified: ticket.customer_notified ? 'Yes' : 'No',
              last_customer_contact: ticket.last_customer_contact || 'N/A'
            }
          } catch (error) {
            console.error(`Failed to fetch details for ticket ${ticket.id}:`, error)
            return {
              ticket_number: ticket.ticket_number,
              title: ticket.title,
              description: ticket.description,
              status: ticket.status,
              priority: ticket.priority,
              category: ticket.category,
              customer_name: 'Error loading details',
              error: 'Failed to load ticket details'
            }
          }
        })
      )

      batchResults.forEach((result) => {
        if (result.status === 'fulfilled') {
          detailedTickets.push(result.value)
        }
      })

      if (i + batchSize < tickets.length) {
        await new Promise(resolve => setTimeout(resolve, 100))
      }
    }

    return detailedTickets
  } catch (error) {
    console.error('Failed to fetch ticket details for export:', error)
    showNotification('Failed to load detailed ticket data', 'error')
    return []
  }
}

const exportToExcel = async (data: any) => {
  const workbook = createExcelWorkbook(data)
  const timestamp = new Date().toISOString().split('T')[0]
  const filename = `trouble-ticket-report-${timestamp}.xlsx`
  downloadExcelFile(workbook, filename)
  showNotification('Excel report exported successfully!', 'success')
}

const exportToCSV = async (data: any) => {
  let csvContent = generateCSVContent(data)
  const timestamp = new Date().toISOString().split('T')[0]
  const filename = `trouble-ticket-report-${timestamp}.csv`
  downloadCSVFile(csvContent, filename)
  showNotification('CSV report exported successfully!', 'success')
}

const exportToPDF = async (data: any) => {
  const pdfContent = generatePDFContent(data)
  const timestamp = new Date().toISOString().split('T')[0]
  const filename = `trouble-ticket-report-${timestamp}.pdf`
  downloadPDFFile(pdfContent, filename)
  showNotification('PDF report exported successfully!', 'success')
}

const exportToJSON = async (data: any) => {
  const timestamp = new Date().toISOString().split('T')[0]
  const filename = `trouble-ticket-report-${timestamp}.json`
  downloadJSONFile(data, filename)
  showNotification('JSON report exported successfully!', 'success')
}

// Excel Helper Functions
const createExcelWorkbook = (data: any): ExcelSheet[] => {
  const sheets: ExcelSheet[] = []

  sheets.push({
    name: 'Summary',
    data: [
      ['Trouble Ticket Analysis Report', '', '', ''],
      ['Generated:', new Date().toLocaleString(), '', ''],
      ['Period:', `${data.metadata.period.from} - ${data.metadata.period.to}`, '', ''],
      ['', '', '', ''],
      ['Key Metrics', '', '', ''],
      ['Total Tickets:', data.statistics?.total_tickets || 0, '', ''],
      ['Resolution Rate:', `${calculateResolutionRate()}%`, '', ''],
      ['Avg Resolution Time:', formatHours(data.statistics?.avg_resolution_time_hours || null), '', ''],
      ['Open Tickets:', data.statistics?.open_tickets || 0, '', ''],
      ['Resolved Tickets:', data.statistics?.resolved_tickets || 0, '', ''],
    ]
  })

  if (data.category_performance?.length > 0) {
    const categorySheet: string[][] = [
      ['Category', 'Total Tickets', 'Resolved', 'Resolution Rate (%)', 'Avg Resolution Time']
    ]

    data.category_performance.forEach((cat: any) => {
      categorySheet.push([
        cat.category_display,
        cat.total_tickets,
        cat.resolved_tickets,
        cat.resolution_rate_percent,
        formatHours(cat.avg_resolution_hours)
      ])
    })

    sheets.push({ name: 'Category Performance', data: categorySheet })
  }

  if (data.user_performance?.length > 0) {
    const userSheet: string[][] = [
      ['Technician', 'Assigned Tickets', 'Resolved', 'Resolution Rate (%)', 'Avg Resolution Time']
    ]

    data.user_performance.forEach((user: any) => {
      userSheet.push([
        user.user_name,
        user.total_assigned,
        user.resolved_tickets,
        user.resolution_rate_percent,
        formatHours(user.avg_resolution_hours)
      ])
    })

    sheets.push({ name: 'Technician Performance', data: userSheet })
  }

  if (data.monthly_trends?.length > 0) {
    const trendsSheet: string[][] = [
      ['Month', 'Total Tickets', 'Resolved', 'Avg Resolution Time (hours)']
    ]

    data.monthly_trends.forEach((trend: any) => {
      trendsSheet.push([
        trend.month_name,
        trend.statistics.total,
        trend.statistics.resolved,
        trend.statistics.avg_resolution_hours
      ])
    })

    sheets.push({ name: 'Monthly Trends', data: trendsSheet })
  }

  if (data.downtime_analysis) {
    const downtimeSheet: string[][] = [
      ['Downtime Analysis', '', '', ''],
      ['Total Downtime:', formatHours(data.downtime_analysis.overall_statistics.total_downtime_hours), '', ''],
      ['Average Downtime:', formatHours(data.downtime_analysis.overall_statistics.avg_downtime_hours), '', ''],
      ['Maximum Downtime:', formatHours(data.downtime_analysis.overall_statistics.max_downtime_hours), '', ''],
      ['Affected Tickets:', data.downtime_analysis.overall_statistics.tickets_with_downtime, '', ''],
      ['', '', '', ''],
      ['Top Customers by Downtime', '', '', ''],
      ['Customer', 'Ticket Count', 'Total Downtime', 'Avg Downtime']
    ]

    data.downtime_analysis.top_customers.slice(0, 10).forEach((customer: any) => {
      downtimeSheet.push([
        customer.customer_name,
        customer.ticket_count,
        formatHours(customer.total_downtime_hours),
        formatHours(customer.avg_downtime_hours)
      ])
    })

    sheets.push({ name: 'Downtime Analysis', data: downtimeSheet })
  }

  if (data.ticket_details?.length > 0) {
    const ticketDetailsSheet: string[][] = []

    ticketDetailsSheet.push(['Ticket Details with Customer Information'])
    ticketDetailsSheet.push([''])

    ticketDetailsSheet.push([
      'Ticket #',
      'Customer Name',
      'Customer Phone',
      'Customer Address',
      'IP Pelanggan',
      'ID Pelanggan',
      'ONU Power (dBm)',
      'Problem Description',
      'Category',
      'Status',
      'Priority',
      'Total Downtime',
      'Assigned To',
      'Total Actions'
    ])

    data.ticket_details.forEach((ticket: any) => {
      const rowData = [
        ticket.ticket_number || '',
        ticket.customer_name || '',
        ticket.customer_phone || '',
        ticket.customer_address || '',
        ticket.ip_pelanggan || '',
        ticket.id_pelanggan || '',
        ticket.onu_power || '',
        ticket.description || '',
        ticket.category || '',
        ticket.status || '',
        ticket.priority || '',
        ticket.downtime_hours || '0',
        ticket.assigned_to || '',
        (ticket.latest_actions ? ticket.latest_actions.length : 0).toString()
      ]

      while (rowData.length < 14) {
        rowData.push('')
      }

      ticketDetailsSheet.push(rowData)
    })

    sheets.push({ name: 'Ticket Details', data: ticketDetailsSheet })

    const detailedProblemsSheet: string[][] = []

    detailedProblemsSheet.push(['Detailed Problem Information & Actions'])
    detailedProblemsSheet.push([''])

    detailedProblemsSheet.push([
      'Ticket #',
      'Problem Title',
      'Problem Description',
      'Latest Action Description',
      'Problem Summary',
      'Action Summary',
      'Action Date',
      'Taken By',
      'Resolution Notes',
      'Status Changes'
    ])

    data.ticket_details.forEach((ticket: any) => {
      const latestAction = ticket.latest_actions[0]
      const statusChanges = ticket.status_history.length > 0
        ? ticket.status_history.map((h: any) => `${h.old_status} → ${h.new_status}`).join(', ')
        : 'No status changes'

      const rowData = [
        ticket.ticket_number || '',
        ticket.title || '',
        ticket.description || '',
        latestAction?.action_description || 'No actions yet',
        latestAction?.summary_problem || 'No problem summary',
        latestAction?.summary_action || 'No action summary',
        latestAction ? formatDate(latestAction.action_date) : 'N/A',
        latestAction?.taken_by || 'N/A',
        ticket.resolution_notes || 'No resolution notes',
        statusChanges
      ]

      while (rowData.length < 10) {
        rowData.push('')
      }

      detailedProblemsSheet.push(rowData)
    })

    sheets.push({ name: 'Problem Details', data: detailedProblemsSheet })
  }

  return sheets
}

const downloadExcelFile = (sheets: any[], filename: string) => {
  createTrueExcelFile(sheets, filename)
}

const createTrueExcelFile = (sheets: any[], filename: string) => {
  try {
    const excelXML = createExcelXML(sheets)

    const blob = new Blob([excelXML], {
      type: 'application/vnd.ms-excel'
    })

    const link = document.createElement('a')
    if (link.download !== undefined) {
      const url = URL.createObjectURL(blob)
      link.setAttribute('href', url)
      const xlsFilename = filename.replace('.xlsx', '.xls')
      link.setAttribute('download', xlsFilename)
      link.style.visibility = 'hidden'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)

      showNotification(`Excel file downloaded successfully as "${xlsFilename}"!`, 'success')
    }
  } catch (error) {
    console.error('Error creating Excel file:', error)
    showNotification('Failed to create Excel file. Downloading CSV format instead.', 'error')
    createExcelCSVWorkbook(sheets, filename)
  }
}

const createExcelXML = (sheets: any[]) => {
  let xmlContent = `<?xml version="1.0"?>
<?mso-application progid="Excel.Sheet"?>
<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"
 xmlns:o="urn:schemas-microsoft-com:office:office"
 xmlns:x="urn:schemas-microsoft-com:office:excel"
 xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"
 xmlns:html="http://www.w3.org/TR/REC-html40">
  <DocumentProperties xmlns="urn:schemas-microsoft-com:office:office">
    <Title>Trouble Ticket Analysis Report</Title>
    <Subject>Trouble Ticket Analysis</Subject>
    <Author>Artacom FTTH Billing System</Author>
    <Created>${new Date().toISOString()}</Created>
    <Company>Artacom</Company>
  </DocumentProperties>
  <ExcelWorkbook xmlns="urn:schemas-microsoft-com:office:excel">
    <WindowHeight>9000</WindowHeight>
    <WindowWidth>13860</WindowWidth>
    <WindowTopX>240</WindowTopX>
    <WindowTopY>75</WindowTopY>
    <ProtectStructure>False</ProtectStructure>
    <ProtectWindows>False</ProtectWindows>
  </ExcelWorkbook>
  <Styles>
    <Style ss:ID="Default" ss:Name="Normal">
      <Alignment ss:Vertical="Bottom"/>
      <Borders/>
      <Font ss:FontName="Arial" ss:Size="11" ss:Color="#000000"/>
      <Interior/>
      <NumberFormat/>
      <Protection/>
    </Style>
    <Style ss:ID="Header">
      <Font ss:FontName="Arial" ss:Size="12" ss:Bold="1" ss:Color="#FFFFFF"/>
      <Interior ss:Color="#4CAF50" ss:Pattern="Solid"/>
      <Borders>
        <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1"/>
        <Border ss:Position="Left" ss:LineStyle="Continuous" ss:Weight="1"/>
        <Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1"/>
        <Border ss:Position="Top" ss:LineStyle="Continuous" ss:Weight="1"/>
      </Borders>
      <Alignment ss:Horizontal="Center" ss:Vertical="Center"/>
    </Style>
    <Style ss:ID="TicketNumber">
      <Font ss:FontName="Arial" ss:Size="11" ss:Bold="1"/>
      <Interior ss:Color="#E8F5E8" ss:Pattern="Solid"/>
      <Borders>
        <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1"/>
        <Border ss:Position="Left" ss:LineStyle="Continuous" ss:Weight="1"/>
        <Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1"/>
        <Border ss:Position="Top" ss:LineStyle="Continuous" ss:Weight="1"/>
      </Borders>
      <Alignment ss:Horizontal="Center" ss:Vertical="Center"/>
    </Style>
    <Style ss:ID="CustomerName">
      <Font ss:FontName="Arial" ss:Size="11" ss:Bold="1"/>
      <Borders>
        <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1"/>
        <Border ss:Position="Left" ss:LineStyle="Continuous" ss:Weight="1"/>
        <Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1"/>
        <Border ss:Position="Top" ss:LineStyle="Continuous" ss:Weight="1"/>
      </Borders>
    </Style>
    <Style ss:ID="Number">
      <NumberFormat ss:Format="#,##0.00"/>
      <Font ss:FontName="Arial" ss:Size="11"/>
      <Borders>
        <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1"/>
        <Border ss:Position="Left" ss:LineStyle="Continuous" ss:Weight="1"/>
        <Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1"/>
        <Border ss:Position="Top" ss:LineStyle="Continuous" ss:Weight="1"/>
      </Borders>
      <Alignment ss:Horizontal="Right" ss:Vertical="Center"/>
    </Style>
    <Style ss:ID="Centered">
      <Alignment ss:Horizontal="Center" ss:Vertical="Center"/>
      <Font ss:FontName="Arial" ss:Size="11" ss:Bold="1"/>
      <Borders>
        <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1"/>
        <Border ss:Position="Left" ss:LineStyle="Continuous" ss:Weight="1"/>
        <Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1"/>
        <Border ss:Position="Top" ss:LineStyle="Continuous" ss:Weight="1"/>
      </Borders>
    </Style>
    <Style ss:ID="DefaultCell">
      <Font ss:FontName="Arial" ss:Size="11"/>
      <Borders>
        <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1"/>
        <Border ss:Position="Left" ss:LineStyle="Continuous" ss:Weight="1"/>
        <Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1"/>
        <Border ss:Position="Top" ss:LineStyle="Continuous" ss:Weight="1"/>
      </Borders>
    </Style>
  </Styles>
`

  sheets.forEach(sheet => {
    xmlContent += createWorksheetXML(sheet)
  })

  xmlContent += '</Workbook>'
  return xmlContent
}

const createWorksheetXML = (sheet: ExcelSheet) => {
  let worksheetXML = `<Worksheet ss:Name="${sheet.name.replace(/[^\w\s-]/g, '_')}">`
  worksheetXML += '<Table>'

  let rowIndex = 0
  sheet.data.forEach((row: any[]) => {
    if (row.length === 0) {
      return
    }

    const isHeaderRow = row.some(cell => {
      const cellStr = String(cell).toLowerCase()
      return cellStr.includes('ticket') && cellStr.includes('#') ||
             cellStr.includes('customer name') ||
             cellStr.includes('problem title') ||
             cellStr.includes('metric') ||
             cellStr.includes('category')
    })

    if (row.length === 1 && (row[0].includes('Details') || row[0].includes('Analysis') || row[0].includes('Summary'))) {
      return
    }

    worksheetXML += '<Row>'
    row.forEach((cell, colIndex) => {
      let cellStyle = 'Default'
      let cellValue = cell === null || cell === undefined ? '' : String(cell)

      if (isHeaderRow) {
        cellStyle = 'Header'
      } else if (sheet.name === 'Ticket_Details') {
        if (colIndex === 0) cellStyle = 'TicketNumber'
        else if (colIndex === 1) cellStyle = 'CustomerName'
        else if (colIndex === 9) cellStyle = 'Centered'
        else if (colIndex === 10) cellStyle = 'Centered'
        else if (colIndex === 11) cellStyle = 'Number'
        else if (colIndex === 13) cellStyle = 'Number'
        else cellStyle = 'DefaultCell'
      } else if (sheet.name === 'Problem_Details') {
        if (colIndex === 0) cellStyle = 'TicketNumber'
        else if (colIndex === 6) cellStyle = 'DefaultCell'
        else cellStyle = 'DefaultCell'
      } else {
        cellStyle = 'DefaultCell'
      }

      const isNumeric = !isHeaderRow && !isNaN(parseFloat(String(cellValue))) && String(cellValue) !== '' && !isNaN(Number(cellValue))

      let processedCellValue: string | number = cellValue
      if (isNumeric) {
        processedCellValue = parseFloat(String(cellValue))
      }

      const cellType = isNumeric ? ('Number' as const) : ('String' as const)

      worksheetXML += `<Cell ss:StyleID="${cellStyle}"><Data ss:Type="${cellType}">${escapeXML(processedCellValue)}</Data></Cell>`
    })
    worksheetXML += '</Row>'
    rowIndex++
  })

  worksheetXML += '</Table></Worksheet>'
  return worksheetXML
}

const escapeXML = (text: any): string => {
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

const createExcelCSVWorkbook = (sheets: ExcelSheet[], filename: string) => {
  let csvContent = ''

  sheets.forEach((sheet, sheetIndex) => {
    if (sheetIndex > 0) {
      csvContent += '\n\n'
    }

    csvContent += `# Sheet: ${sheet.name}\n`

    sheet.data.forEach((row: string[], rowIndex: number) => {
      if (row.length === 0 || (row.length === 1 && row[0].includes('Details'))) {
        return
      }

      if (rowIndex === 0 || (rowIndex === 1 && !row[0].includes('#'))) {
        return
      }

      if (rowIndex === 2 || (row.some(cell => String(cell).includes('#')))) {
        const headerRow = row.map(cell => `"${String(cell)}"`).join(',')
        csvContent += headerRow + '\n'
      } else {
        const dataRow = row.map(cell => {
          if (cell === null || cell === undefined) return '""'
          return `"${String(cell).replace(/"/g, '""')}"`
        }).join(',')
        csvContent += dataRow + '\n'
      }
    })
  })

  const blob = new Blob([csvContent], {
    type: 'text/csv;charset=utf-8;'
  })

  const link = document.createElement('a')
  if (link.download !== undefined) {
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)

    const csvFilename = filename.replace('.xlsx', '.csv')
    link.setAttribute('download', csvFilename)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    showNotification(`Excel-compatible CSV file downloaded as "${csvFilename}". Open with Excel for proper formatting.`, 'success')
  }
}

// CSV Helper Functions
const generateCSVContent = (data: any): string => {
  let csvContent = `Trouble Ticket Analysis Report\n`
  csvContent += `Generated: ${new Date().toLocaleString()}\n`
  csvContent += `Period: ${data.metadata.period.from} - ${data.metadata.period.to}\n\n`

  csvContent += `SUMMARY\n`
  csvContent += `Metric,Value\n`
  csvContent += `Total Tickets,${data.statistics?.total_tickets || 0}\n`
  csvContent += `Resolution Rate,${calculateResolutionRate()}%\n`
  csvContent += `Avg Resolution Time,${formatHours(data.statistics?.avg_resolution_time_hours || null)}\n`
  csvContent += `Open Tickets,${data.statistics?.open_tickets || 0}\n`
  csvContent += `Resolved Tickets,${data.statistics?.resolved_tickets || 0}\n\n`

  if (data.category_performance?.length > 0) {
    csvContent += `CATEGORY PERFORMANCE\n`
    csvContent += `Category,Total Tickets,Resolved,Resolution Rate (%),Avg Resolution Time\n`

    data.category_performance.forEach((cat: any) => {
      csvContent += `"${cat.category_display}",${cat.total_tickets},${cat.resolved_tickets},${cat.resolution_rate_percent},"${formatHours(cat.avg_resolution_hours)}"\n`
    })
    csvContent += `\n`
  }

  if (data.user_performance?.length > 0) {
    csvContent += `TECHNICIAN PERFORMANCE\n`
    csvContent += `Technician,Assigned Tickets,Resolved,Resolution Rate (%),Avg Resolution Time\n`

    data.user_performance.forEach((user: any) => {
      csvContent += `"${user.user_name}",${user.total_assigned},${user.resolved_tickets},${user.resolution_rate_percent},"${formatHours(user.avg_resolution_hours)}"\n`
    })
    csvContent += `\n`
  }

  if (data.monthly_trends?.length > 0) {
    csvContent += `MONTHLY TRENDS\n`
    csvContent += `Month,Total Tickets,Resolved,Avg Resolution Time (hours)\n`

    data.monthly_trends.forEach((trend: any) => {
      csvContent += `"${trend.month_name}",${trend.statistics.total},${trend.statistics.resolved},${trend.statistics.avg_resolution_hours}\n`
    })
    csvContent += `\n`
  }

  if (data.downtime_analysis) {
    csvContent += `DOWNTIME ANALYSIS\n`
    csvContent += `Metric,Value\n`
    csvContent += `Total Downtime,${formatHours(data.downtime_analysis.overall_statistics.total_downtime_hours)}\n`
    csvContent += `Average Downtime,${formatHours(data.downtime_analysis.overall_statistics.avg_downtime_hours)}\n`
    csvContent += `Maximum Downtime,${formatHours(data.downtime_analysis.overall_statistics.max_downtime_hours)}\n`
    csvContent += `Affected Tickets,${data.downtime_analysis.overall_statistics.tickets_with_downtime}\n\n`

    if (data.downtime_analysis.top_customers?.length > 0) {
      csvContent += `TOP CUSTOMERS BY DOWNTIME\n`
      csvContent += `Customer,Ticket Count,Total Downtime,Avg Downtime\n`

      data.downtime_analysis.top_customers.slice(0, 10).forEach((customer: any) => {
        csvContent += `"${customer.customer_name}",${customer.ticket_count},"${formatHours(customer.total_downtime_hours)}","${formatHours(customer.avg_downtime_hours)}"\n`
      })
    }
  }

  if (data.ticket_details?.length > 0) {
    csvContent += `\nTROUBLE TICKET DETAILS\n`
    csvContent += `Ticket Number,Customer Name,Customer Address,Phone,Email,Brand,ID Pelanggan,IP Pelanggan,ONU Power,Status,Priority,Category,Assigned To,Created,Resolved,Downtime Hours,Problem Description,Resolution Notes,Total Actions\n`

    data.ticket_details.forEach((ticket: any) => {
      csvContent += `"${ticket.ticket_number}","${ticket.customer_name}","${ticket.customer_address}","${ticket.customer_phone}","${ticket.customer_email}","${ticket.customer_brand}","${ticket.id_pelanggan}","${ticket.ip_pelanggan}","${ticket.onu_power}","${ticket.status}","${ticket.priority}","${ticket.category}","${ticket.assigned_to}","${formatDate(ticket.created_at)}","${formatDate(ticket.resolved_at)}","${ticket.downtime_hours}","${ticket.description.substring(0, 200).replace(/"/g, '""')}","${ticket.resolution_notes.replace(/"/g, '""')}","${ticket.latest_actions.length}"\n`
    })

    csvContent += `\nTICKET ACTION DETAILS\n`
    csvContent += `Ticket Number,Action Date,Action Description,Problem Summary,Action Summary,Taken By\n`

    data.ticket_details.forEach((ticket: any) => {
      if (ticket.latest_actions.length > 0) {
        ticket.latest_actions.forEach((action: any) => {
          csvContent += `"${ticket.ticket_number}","${formatDate(action.action_date)}","${action.action_description.replace(/"/g, '""')}","${action.summary_problem.replace(/"/g, '""')}","${action.summary_action.replace(/"/g, '""')}","${action.taken_by}"\n`
        })
      } else {
        csvContent += `"${ticket.ticket_number}","No actions recorded","-","-","-","-"\n`
      }
    })

    csvContent += `\nTICKET STATUS HISTORY\n`
    csvContent += `Ticket Number,Changed Date,Old Status,New Status,Changed By,Notes\n`

    data.ticket_details.forEach((ticket: any) => {
      if (ticket.status_history.length > 0) {
        ticket.status_history.forEach((history: any) => {
          csvContent += `"${ticket.ticket_number}","${formatDate(history.changed_date)}","${history.old_status}","${history.new_status}","${history.changed_by}","${history.notes.replace(/"/g, '""')}"\n`
        })
      } else {
        csvContent += `"${ticket.ticket_number}","No status changes recorded","-","-","-","-"\n`
      }
    })
  }

  return csvContent
}

const downloadCSVFile = (content: string, filename: string) => {
  const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')

  if (link.download !== undefined) {
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', filename)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }
}

// PDF Helper Functions
const generatePDFContent = (data: any): string => {
  let htmlContent = `
    <!DOCTYPE html>
    <html>
    <head>
      <title>Trouble Ticket Report</title>
      <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { text-align: center; margin-bottom: 30px; }
        .section { margin-bottom: 25px; }
        .section h2 { color: #1976d2; border-bottom: 2px solid #1976d2; padding-bottom: 5px; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 15px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f5f5f5; font-weight: bold; }
        .summary-metric { display: inline-block; margin: 10px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .metric-value { font-size: 24px; font-weight: bold; color: #1976d2; }
        .metric-label { font-size: 12px; color: #666; }
      </style>
    </head>
    <body>
      <div class="header">
        <h1>Trouble Ticket Analysis Report</h1>
        <p>Generated: ${new Date().toLocaleString()}</p>
        <p>Period: ${data.metadata.period.from} - ${data.metadata.period.to}</p>
      </div>

      <div class="section">
        <h2>Summary</h2>
        <div class="summary-metric">
          <div class="metric-value">${data.statistics?.total_tickets || 0}</div>
          <div class="metric-label">Total Tickets</div>
        </div>
        <div class="summary-metric">
          <div class="metric-value">${calculateResolutionRate()}%</div>
          <div class="metric-label">Resolution Rate</div>
        </div>
        <div class="summary-metric">
          <div class="metric-value">${formatHours(data.statistics?.avg_resolution_time_hours || null)}</div>
          <div class="metric-label">Avg Resolution Time</div>
        </div>
      </div>
  `

  if (data.category_performance?.length > 0) {
    htmlContent += `
      <div class="section">
        <h2>Category Performance</h2>
        <table>
          <thead>
            <tr>
              <th>Category</th>
              <th>Total</th>
              <th>Resolved</th>
              <th>Resolution Rate</th>
              <th>Avg Resolution Time</th>
            </tr>
          </thead>
          <tbody>
    `

    data.category_performance.forEach((cat: any) => {
      htmlContent += `
        <tr>
          <td>${cat.category_display}</td>
          <td>${cat.total_tickets}</td>
          <td>${cat.resolved_tickets}</td>
          <td>${cat.resolution_rate_percent}%</td>
          <td>${formatHours(cat.avg_resolution_hours)}</td>
        </tr>
      `
    })

    htmlContent += `
          </tbody>
        </table>
      </div>
    `
  }

  if (data.user_performance?.length > 0) {
    htmlContent += `
      <div class="section">
        <h2>Technician Performance</h2>
        <table>
          <thead>
            <tr>
              <th>Technician</th>
              <th>Assigned</th>
              <th>Resolved</th>
              <th>Resolution Rate</th>
              <th>Avg Resolution Time</th>
            </tr>
          </thead>
          <tbody>
    `

    data.user_performance.forEach((user: any) => {
      htmlContent += `
        <tr>
          <td>${user.user_name}</td>
          <td>${user.total_assigned}</td>
          <td>${user.resolved_tickets}</td>
          <td>${user.resolution_rate_percent}%</td>
          <td>${formatHours(user.avg_resolution_hours)}</td>
        </tr>
      `
    })

    htmlContent += `
          </tbody>
        </table>
      </div>
    `
  }

  if (data.ticket_details?.length > 0) {
    htmlContent += `
      <div class="section">
        <h2>Trouble Ticket Details (Latest 20)</h2>
        <table>
          <thead>
            <tr>
              <th>Ticket #</th>
              <th>Customer</th>
              <th>Problem</th>
              <th>Status</th>
              <th>Downtime</th>
              <th>Assigned To</th>
            </tr>
          </thead>
          <tbody>
    `

    data.ticket_details.slice(0, 20).forEach((ticket: any) => {
      htmlContent += `
        <tr>
          <td>${ticket.ticket_number}</td>
          <td>${ticket.customer_name}</td>
          <td>${ticket.description.substring(0, 100)}${ticket.description.length > 100 ? '...' : ''}</td>
          <td>${ticket.status}</td>
          <td>${ticket.downtime_hours}h</td>
          <td>${ticket.assigned_to}</td>
        </tr>
      `
    })

    htmlContent += `
          </tbody>
        </table>
        ${data.ticket_details.length > 20 ? `<p><em>*Showing 20 of ${data.ticket_details.length} total tickets. Use Excel or CSV export for complete data.</em></p>` : ''}
      </div>
    `
  }

  htmlContent += `
    </body>
    </html>
  `

  return htmlContent
}

const downloadPDFFile = (htmlContent: string, filename: string) => {
  const printWindow = window.open('', '_blank', 'width=1000,height=800')
  if (printWindow) {
    printWindow.document.write(htmlContent)
    printWindow.document.close()
    printWindow.focus()

    printWindow.onload = () => {
      setTimeout(() => {
        printWindow.print()

        showNotification('Print dialog opened. Choose "Save as PDF" as the destination.', 'info')

        printWindow.onafterprint = () => {
          printWindow.close()
        }
      }, 1000)
    }
  } else {
    showNotification('Please allow popups for this site to use PDF export.', 'warning')

    const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8;' })
    const link = document.createElement('a')

    if (link.download !== undefined) {
      const url = URL.createObjectURL(blob)
      link.setAttribute('href', url)
      link.setAttribute('download', filename.replace('.pdf', '.html'))
      link.style.visibility = 'hidden'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)

      showNotification('HTML file downloaded. Open and print to PDF.', 'info')
    }
  }
}

// JSON Helper Functions
const downloadJSONFile = (data: any, filename: string) => {
  const jsonString = JSON.stringify(data, null, 2)
  const blob = new Blob([jsonString], { type: 'application/json;charset=utf-8;' })
  const link = document.createElement('a')

  if (link.download !== undefined) {
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', filename)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }
}

// Watch for changes
watch(trendPeriod, () => {
  loadMonthlyTrends()
})

// Lifecycle
onMounted(() => {
  refreshAllData()
})
</script>

<style scoped>
/* ===== GLOBAL STYLES ===== */
* {
  box-sizing: border-box;
}

/* ===== ANIMATIONS ===== */
@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

@keyframes slideOut {
  from {
    transform: translateX(0);
    opacity: 1;
  }
  to {
    transform: translateX(100%);
    opacity: 0;
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}

/* ===== CONTAINER ===== */
.trouble-ticket-report-container {
  padding: 32px;
  background: linear-gradient(135deg,
    rgb(var(--v-theme-background)) 0%,
    rgba(var(--v-theme-surface), 0.4) 100%);
  min-height: 100vh;
}

/* ===== ENHANCED HEADER ===== */
.page-header {
  background: linear-gradient(135deg,
    rgba(var(--v-theme-primary), 0.1) 0%,
    rgba(var(--v-theme-secondary), 0.05) 100%);
  border-radius: 24px;
  padding: 40px;
  margin-bottom: 32px;
  border: 1px solid rgba(var(--v-theme-primary), 0.15);
  box-shadow: 
    0 8px 32px rgba(var(--v-theme-shadow), 0.1),
    0 2px 8px rgba(var(--v-theme-shadow), 0.05);
  animation: fadeInUp 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 32px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 24px;
  flex: 1;
}

.header-icon-wrapper {
  position: relative;
}

.header-avatar {
  background: linear-gradient(135deg,
    rgb(var(--v-theme-primary)) 0%,
    rgb(var(--v-theme-secondary)) 100%) !important;
  box-shadow: 
    0 8px 24px rgba(var(--v-theme-primary), 0.3),
    0 0 0 4px rgba(var(--v-theme-primary), 0.1);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.header-avatar:hover {
  transform: translateY(-4px);
  box-shadow: 
    0 12px 32px rgba(var(--v-theme-primary), 0.4),
    0 0 0 6px rgba(var(--v-theme-primary), 0.15);
}

.header-text {
  flex: 1;
}

.page-title {
  font-size: 2.5rem;
  font-weight: 800;
  margin: 0 0 12px 0;
  line-height: 1.2;
  letter-spacing: -0.5px;
}

.title-gradient {
  background: linear-gradient(135deg,
    rgb(var(--v-theme-primary)) 0%,
    rgb(var(--v-theme-secondary)) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.title-gradient-modern {
  background: linear-gradient(135deg,
    #667eea 0%,
    #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.title-accent {
  color: #FF6B6B;
  font-weight: 700;
}

.title-solid {
  color: #667eea;
  font-weight: 700;
}

.title-normal {
  color: rgb(var(--v-theme-on-surface));
}

.page-subtitle {
  font-size: 1.05rem;
  color: rgba(var(--v-theme-on-surface), 0.9);
  margin: 0;
  font-weight: 500;
  display: flex;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 12px;
  flex-shrink: 0;
}

.refresh-btn {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.refresh-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(var(--v-theme-primary), 0.3);
}

.export-btn {
  box-shadow: 0 4px 12px rgba(var(--v-theme-primary), 0.3);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.load-tickets-btn {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.load-tickets-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(var(--v-theme-primary), 0.4);
}

.export-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(var(--v-theme-primary), 0.4);
}

/* Modern Button Styling */
.modern-btn {
  position: relative;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  text-transform: none;
  font-weight: 600;
}

.modern-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.1),
    transparent
  );
  transition: left 0.5s;
}

.modern-btn:hover::before {
  left: 100%;
}

.modern-btn:hover {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 8px 25px rgba(var(--v-theme-primary), 0.3);
}

.modern-btn:active {
  transform: translateY(0) scale(0.98);
}

.refresh-btn-modern:hover {
  box-shadow: 0 8px 25px rgba(var(--v-theme-primary), 0.3);
}

.export-btn-modern:hover {
  box-shadow: 0 8px 25px rgba(var(--v-theme-success), 0.3);
}

.btn-text {
  position: relative;
  z-index: 1;
}

/* ===== ENHANCED DATE FILTER ===== */
.date-filter-card {
  background: rgb(var(--v-theme-surface));
  border-radius: 20px;
  border: 1px solid rgba(var(--v-theme-outline), 0.1);
  margin-bottom: 32px;
  box-shadow: 
    0 4px 20px rgba(var(--v-theme-shadow), 0.08),
    0 1px 4px rgba(var(--v-theme-shadow), 0.04);
  animation: fadeInUp 0.6s cubic-bezier(0.4, 0, 0.2, 1) 0.1s both;
}

.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.filter-title-wrapper {
  display: flex;
  align-items: center;
  gap: 16px;
}

.filter-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(135deg,
    rgba(var(--v-theme-primary), 0.1) 0%,
    rgba(var(--v-theme-secondary), 0.1) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.filter-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
  margin: 0;
}

.filter-subtitle {
  font-size: 0.875rem;
  color: rgba(var(--v-theme-on-surface), 0.85);
  margin: 4px 0 0 0;
}

.active-filter-chip {
  box-shadow: 0 2px 8px rgba(var(--v-theme-primary), 0.2);
  animation: pulse 2s infinite;
}

.date-input, .filter-select {
  transition: all 0.3s ease;
}

.date-input:hover, .filter-select:hover {
  transform: translateY(-2px);
}

.clear-filter-btn {
  transition: all 0.3s ease;
}

.clear-filter-btn:hover:not(:disabled) {
  transform: translateY(-2px);
}

/* ===== ENHANCED METRICS OVERVIEW ===== */
.metrics-overview {
  margin-bottom: 32px;
  animation: fadeInUp 0.6s cubic-bezier(0.4, 0, 0.2, 1) 0.2s both;
}

.section-header {
  margin-bottom: 24px;
}

.section-header-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.section-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(135deg,
    rgba(var(--v-theme-primary), 0.1) 0%,
    rgba(var(--v-theme-secondary), 0.1) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px;
}

.section-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
  margin: 0;
}

.section-subtitle {
  font-size: 0.95rem;
  color: rgba(var(--v-theme-on-surface), 0.85);
  margin: 4px 0 0 0;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
}

.metric-card {
  background: rgb(var(--v-theme-surface));
  border-radius: 20px;
  border: 1px solid rgba(var(--v-theme-outline), 0.1);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  position: relative;
  animation: fadeInUp 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.metric-card:nth-child(1) { animation-delay: 0.1s; }
.metric-card:nth-child(2) { animation-delay: 0.2s; }
.metric-card:nth-child(3) { animation-delay: 0.3s; }
.metric-card:nth-child(4) { animation-delay: 0.4s; }

.metric-card:hover {
  transform: translateY(-8px);
  box-shadow: 
    0 20px 40px rgba(var(--v-theme-shadow), 0.15),
    0 8px 16px rgba(var(--v-theme-shadow), 0.1);
  border-color: rgba(var(--v-theme-primary), 0.2);
}

.metric-gradient {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 5px;
}

.gradient-blue {
  background: linear-gradient(90deg,
    #2196F3 0%,
    #21CBF3 100%);
}

.gradient-green {
  background: linear-gradient(90deg,
    #4CAF50 0%,
    #8BC34A 100%);
}

.gradient-orange {
  background: linear-gradient(90deg,
    #FF9800 0%,
    #FFC107 100%);
}

.gradient-red {
  background: linear-gradient(90deg,
    #F44336 0%,
    #E91E63 100%);
}

.metric-content {
  display: flex;
  align-items: center;
  padding: 32px 28px 24px !important;
  gap: 20px;
}

.metric-icon-wrapper {
  width: 72px;
  height: 72px;
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  transition: all 0.3s ease;
}

.metric-card:hover .metric-icon-wrapper {
  transform: scale(1.1) rotate(5deg);
}

.blue-gradient {
  background: linear-gradient(135deg, #2196F3 0%, #21CBF3 100%);
}

.green-gradient {
  background: linear-gradient(135deg, #4CAF50 0%, #8BC34A 100%);
}

.orange-gradient {
  background: linear-gradient(135deg, #FF9800 0%, #FFC107 100%);
}

.red-gradient {
  background: linear-gradient(135deg, #F44336 0%, #E91E63 100%);
}

.metric-info {
  flex: 1;
}

.metric-value {
  font-size: 2.5rem;
  font-weight: 800;
  color: rgb(var(--v-theme-on-surface));
  line-height: 1;
  margin-bottom: 8px;
}

.metric-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.9);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 12px;
}

.metric-change {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8rem;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 8px;
  display: inline-flex;
}

.metric-change.positive {
  color: rgb(var(--v-theme-success));
  background: rgba(var(--v-theme-success), 0.1);
}

.metric-change.warning {
  color: rgb(var(--v-theme-warning));
  background: rgba(var(--v-theme-warning), 0.1);
}

.metric-change.negative {
  color: rgb(var(--v-theme-error));
  background: rgba(var(--v-theme-error), 0.1);
}

.metric-footer {
  padding: 12px 28px;
  /* PERUBAHAN: Mengganti background abu-abu dengan warna outline yang sangat halus */
  background: rgba(var(--v-theme-outline), 0.05);
  border-top: 1px solid rgba(var(--v-theme-outline), 0.1);
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.85);
}

/* ===== ENHANCED CHARTS ===== */
.charts-section {
  margin-bottom: 32px;
  animation: fadeInUp 0.6s cubic-bezier(0.4, 0, 0.2, 1) 0.3s both;
}

.chart-card {
  background: rgb(var(--v-theme-surface));
  border-radius: 20px;
  border: 1px solid rgba(var(--v-theme-outline), 0.1);
  overflow: hidden;
  box-shadow: 
    0 4px 20px rgba(var(--v-theme-shadow), 0.08),
    0 1px 4px rgba(var(--v-theme-shadow), 0.04);
  transition: all 0.3s ease;
}

.chart-card:hover {
  box-shadow: 
    0 8px 32px rgba(var(--v-theme-shadow), 0.12),
    0 2px 8px rgba(var(--v-theme-shadow), 0.06);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 28px !important;
  /* PERUBAHAN: Menghapus background abu-abu */
  /* background: rgba(var(--v-theme-surface-variant), 0.3); */
}

.chart-title-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chart-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
  margin: 0;
}

.chart-subtitle {
  font-size: 0.875rem;
  color: rgba(var(--v-theme-on-surface), 0.8);
  margin: 4px 0 0 0;
}

.period-toggle {
  border-radius: 10px;
  overflow: hidden;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px;
  gap: 20px;
}

.loading-text {
  font-size: 1rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  font-weight: 500;
  margin: 0;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px;
  gap: 16px;
}

.empty-state-icon {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  /* PERUBAHAN: Mengganti background abu-abu dengan warna outline yang sangat halus */
  background: rgba(var(--v-theme-outline), 0.05);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
}

.empty-state-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin: 0;
}

.empty-state-text {
  font-size: 0.875rem;
  color: rgba(var(--v-theme-on-surface), 0.8);
  margin: 0;
}

/* ===== ENHANCED TABLES ===== */
.tables-section {
  margin-bottom: 32px;
  animation: fadeInUp 0.6s cubic-bezier(0.4, 0, 0.2, 1) 0.4s both;
}

.table-card {
  background: rgb(var(--v-theme-surface));
  border-radius: 20px;
  border: 1px solid rgba(var(--v-theme-outline), 0.1);
  overflow: hidden;
  box-shadow: 
    0 4px 20px rgba(var(--v-theme-shadow), 0.08),
    0 1px 4px rgba(var(--v-theme-shadow), 0.04);
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 28px !important;
  /* PERUBAHAN: Menghapus background abu-abu */
  /* background: rgba(var(--v-theme-surface-variant), 0.3); */
}

.table-title-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}

.table-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
  margin: 0;
}

.table-subtitle {
  font-size: 0.875rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin: 4px 0 0 0;
}

.enhanced-table :deep(.v-data-table__tr) {
  transition: all 0.2s ease;
}

.enhanced-table :deep(.v-data-table__tr:hover) {
  background-color: rgba(var(--v-theme-primary), 0.05) !important;
  transform: scale(1.01);
}

.category-chip {
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.progress-wrapper {
  padding: 4px 0;
}

.resolution-progress {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.progress-text {
  font-size: 0.75rem;
  color: white !important;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.user-info, .customer-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar, .customer-avatar {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.user-initial, .customer-initial {
  font-size: 0.875rem;
  font-weight: 700;
  color: white;
}

.user-name, .customer-name {
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

/* ===== ENHANCED DOWNTIME SECTION ===== */
.downtime-section {
  margin-bottom: 32px;
  animation: fadeInUp 0.6s cubic-bezier(0.4, 0, 0.2, 1) 0.5s both;
}

.downtime-card {
  background: rgb(var(--v-theme-surface));
  border-radius: 20px;
  border: 1px solid rgba(var(--v-theme-outline), 0.1);
  overflow: hidden;
  box-shadow: 
    0 4px 20px rgba(var(--v-theme-shadow), 0.08),
    0 1px 4px rgba(var(--v-theme-shadow), 0.04);
}

.downtime-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 28px !important;
  /* PERUBAHAN: Menghapus background abu-abu */
  /* background: rgba(var(--v-theme-surface-variant), 0.3); */
}

.downtime-title-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}

.downtime-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
  margin: 0;
}

.downtime-subtitle {
  font-size: 0.875rem;
  color: rgba(var(--v-theme-on-surface), 0.85);
  margin: 4px 0 0 0;
}

.downtime-overview {
  margin-bottom: 32px;
}

.subsection-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 20px;
  display: flex;
  align-items: center;
}

.downtime-metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.downtime-metric-card {
  /* PERUBAHAN: Mengganti background abu-abu dengan warna outline yang sangat halus */
  background: rgba(var(--v-theme-outline), 0.04);
  border-radius: 16px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  /* PERUBAHAN: Mempertegas border agar tetap terlihat */
  border: 1px solid rgba(var(--v-theme-outline), 0.12);
  transition: all 0.3s ease;
}

.downtime-metric-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(var(--v-theme-shadow), 0.12);
}

.downtime-metric-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.blue-bg {
  background: linear-gradient(135deg, #2196F3 0%, #21CBF3 100%);
}

.green-bg {
  background: linear-gradient(135deg, #4CAF50 0%, #8BC34A 100%);
}

.orange-bg {
  background: linear-gradient(135deg, #FF9800 0%, #FFC107 100%);
}

.red-bg {
  background: linear-gradient(135deg, #F44336 0%, #E91E63 100%);
}

.downtime-metric-info {
  flex: 1;
}

.downtime-metric-value {
  font-size: 1.75rem;
  font-weight: 700;
  color: rgb(var(--v-theme-primary));
  margin-bottom: 4px;
}

.downtime-metric-label {
  font-size: 0.875rem;
  color: rgba(var(--v-theme-on-surface), 0.9);
  font-weight: 500;
}

.top-customers {
  margin-top: 32px;
}

.downtime-chip {
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* ===== ENHANCED TICKET DETAILS SECTION ===== */
.ticket-details-section {
  margin-bottom: 32px;
  animation: fadeInUp 0.6s cubic-bezier(0.4, 0, 0.2, 1) 0.6s both;
}

.ticket-details-card {
  background: rgb(var(--v-theme-surface));
  border-radius: 20px;
  border: 1px solid rgba(var(--v-theme-outline), 0.1);
  overflow: hidden;
  box-shadow: 
    0 4px 20px rgba(var(--v-theme-shadow), 0.08),
    0 1px 4px rgba(var(--v-theme-shadow), 0.04);
}

.ticket-details-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 28px !important;
  /* PERUBAHAN: Menghapus background abu-abu */
  /* background: rgba(var(--v-theme-surface-variant), 0.3); */
}

.ticket-details-title-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.ticket-details-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
  margin: 0;
}

.ticket-details-subtitle {
  font-size: 0.875rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin: 4px 0 0 0;
}

.ticket-details-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ticket-filters-card {
  /* PERUBAHAN: Mengganti background abu-abu dengan warna outline yang sangat halus */
  background: rgba(var(--v-theme-outline), 0.04);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 24px;
  /* PERUBAHAN: Mempertegas border agar tetap terlihat */
  border: 1px solid rgba(var(--v-theme-outline), 0.12);
}

.search-field, .filter-select {
  transition: all 0.3s ease;
}

.search-field:hover, .filter-select:hover {
  transform: translateY(-2px);
}

.ticket-number-chip {
  font-weight: 700;
  box-shadow: 0 2px 8px rgba(var(--v-theme-primary), 0.2);
}

.customer-info-cell {
  line-height: 1.6;
}

.customer-name-row {
  display: flex;
  align-items: center;
  margin-bottom: 6px;
}

.customer-name-text {
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  font-size: 0.95rem;
}

.customer-detail-row {
  display: flex;
  align-items: center;
  margin-bottom: 4px;
}

.customer-detail-text {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.9);
}

.technical-info-cell {
  line-height: 1.6;
}

.tech-detail-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.tech-label {
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.9);
  font-size: 0.75rem;
  min-width: 28px;
}

.tech-chip {
  font-family: monospace;
  font-weight: 600;
}

.problem-cell {
  line-height: 1.6;
}

.problem-title-text {
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 6px;
  font-size: 0.95rem;
}

.problem-description-text {
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.9);
  margin-bottom: 8px;
  line-height: 1.4;
}

.problem-category-chip {
  font-weight: 600;
}

.status-priority-cell {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.status-chip, .priority-chip {
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.downtime-cell {
  text-align: center;
}

.downtime-chip-main {
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 4px;
}

.downtime-minutes {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.85);
}

.assignment-cell {
  line-height: 1.6;
}

.assigned-user-row {
  display: flex;
  align-items: center;
  margin-bottom: 6px;
}

.assigned-user-text {
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  font-size: 0.9rem;
}

.action-count-chip {
  font-weight: 600;
}

/* ===== ENHANCED EXPORT DIALOG ===== */
.export-dialog :deep(.v-overlay__content) {
  animation: fadeInUp 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.export-dialog-card {
  border-radius: 24px !important;
  overflow: hidden;
}

.export-dialog-header {
  background: linear-gradient(135deg,
    rgba(var(--v-theme-primary), 0.1) 0%,
    rgba(var(--v-theme-secondary), 0.05) 100%);
  padding: 28px 32px !important;
}

.export-header-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

.export-icon-wrapper {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  background: linear-gradient(135deg,
    rgb(var(--v-theme-primary)) 0%,
    rgb(var(--v-theme-secondary)) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 24px rgba(var(--v-theme-primary), 0.3);
}

.export-dialog-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
  margin: 0;
}

.export-dialog-subtitle {
  font-size: 0.95rem;
  color: rgba(var(--v-theme-on-surface), 0.85);
  margin: 4px 0 0 0;
}

.export-description {
  font-size: 1rem;
  color: rgba(var(--v-theme-on-surface), 0.9);
  margin-bottom: 24px;
}

.export-options-list {
  background: transparent;
  padding: 0;
}

.export-option-item {
  border-radius: 16px;
  margin-bottom: 12px;
  border: 2px solid rgba(var(--v-theme-outline), 0.1);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  padding: 20px 24px !important;
  cursor: pointer;
}

.export-option-item:hover:not([disabled]) {
  background-color: rgba(var(--v-theme-primary), 0.05);
  border-color: rgba(var(--v-theme-primary), 0.3);
  transform: translateX(8px);
  box-shadow: 0 4px 16px rgba(var(--v-theme-shadow), 0.1);
}

.export-option-item:active:not([disabled]) {
  transform: translateX(8px) scale(0.98);
}

.export-format-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.success-bg {
  background: linear-gradient(135deg, #4CAF50 0%, #8BC34A 100%);
}

.info-bg {
  background: linear-gradient(135deg, #2196F3 0%, #21CBF3 100%);
}

.error-bg {
  background: linear-gradient(135deg, #F44336 0%, #E91E63 100%);
}

.warning-bg {
  background: linear-gradient(135deg, #FF9800 0%, #FFC107 100%);
}

.export-format-title {
  font-size: 1.125rem;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 4px;
}

.export-format-description {
  font-size: 0.875rem;
  color: rgba(var(--v-theme-on-surface), 0.85);
  line-height: 1.4;
}

.export-progress-alert {
  border-radius: 12px;
  border: 1px solid rgba(var(--v-theme-info), 0.2);
}

.export-progress-content {
  display: flex;
  align-items: center;
}

.export-dialog-actions {
  /* PERUBAHAN: Mengganti background abu-abu dengan warna outline yang sangat halus */
  background: rgba(var(--v-theme-outline), 0.05);
}

/* ===== RESPONSIVE DESIGN ===== */
@media (max-width: 1200px) {
  .metrics-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .downtime-metrics-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 960px) {
  .header-content {
    flex-direction: column;
    align-items: stretch;
  }

  .header-left {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  .header-actions {
    justify-content: center;
  }
}

@media (max-width: 768px) {
  .trouble-ticket-report-container {
    padding: 20px;
  }

  .page-header {
    padding: 28px 24px;
  }

  .page-title {
    font-size: 2rem;
  }

  .metrics-grid {
    grid-template-columns: 1fr;
  }

  .downtime-metrics-grid {
    grid-template-columns: 1fr;
  }

  .ticket-details-header {
    flex-direction: column;
    align-items: stretch;
    gap: 16px;
  }

  .ticket-details-actions {
    justify-content: space-between;
  }
}

@media (max-width: 600px) {
  .header-actions {
    flex-direction: column;
    width: 100%;
  }

  .header-actions .v-btn {
    width: 100%;
  }

  .date-range-filters .v-row {
    flex-direction: column;
  }

  .filter-header {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
}

/* ===== PRINT STYLES ===== */
@media print {
  .trouble-ticket-report-container {
    padding: 0;
  }

  .page-header,
  .date-filter-card,
  .header-actions,
  .refresh-btn,
  .export-btn,
  .clear-filter-btn {
    display: none !important;
  }

  .metric-card,
  .chart-card,
  .table-card,
  .downtime-card,
  .ticket-details-card {
    break-inside: avoid;
    box-shadow: none !important;
    border: 1px solid #ddd !important;
  }
}
</style>