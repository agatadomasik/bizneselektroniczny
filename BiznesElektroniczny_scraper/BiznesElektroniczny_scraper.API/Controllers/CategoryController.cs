﻿using BiznesElektroniczny_scraper.API.Services;
using BiznesElektroniczny_scraper.API.Services.Scraping;
using Hangfire;
using Microsoft.AspNetCore.Mvc;

namespace BiznesElektroniczny_scraper.API.Controllers;

[Route("api/[controller]")]
[ApiController]
public class CategoryController(
    CategoryRetrieverService categoryRetrieverService,
    CategoryScrapingService categoryScrapingService, ILogger<CategoryController> logger) : ControllerBase {
    [HttpGet]
    public async Task<IActionResult> GetAllCategories() => Ok(await categoryRetrieverService.GetAllCategories());

    [HttpPost("scrape")]
    public IActionResult ScrapeCategories() => Ok(BackgroundJob.Enqueue(() => categoryScrapingService.ScrapeAsync()));

    [HttpGet("flat-categories")]
    public async Task<IActionResult> GetFlatCategories() => Ok(await categoryRetrieverService.GetFlatCategories());
}